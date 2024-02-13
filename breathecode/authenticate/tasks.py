import logging
import os

from celery import shared_task
from django.contrib.auth.models import User

from breathecode.authenticate.models import FirstPartyCredentials, FirstPartyWebhookLog, UserInvite
from breathecode.marketing.actions import validate_email
from breathecode.notify import actions as notify_actions
from breathecode.utils.decorators.task import AbortTask, RetryTask, TaskPriority, task
from breathecode.utils.service import Service
from breathecode.utils.validation_exception import ValidationException

from .actions import add_to_organization, remove_from_organization, set_gitpod_user_expiration

API_URL = os.getenv('API_URL', '')

logger = logging.getLogger(__name__)


@task(bind=True)
def async_validate_email_invite(self, invite_id, task_manager_id, **_):
    logger.debug(f'Validating email for invite {invite_id}')
    user_invite = UserInvite.objects.filter(id=invite_id).first()

    if user_invite is None:
        raise AbortTask(f'UserInvite {invite_id} not found')

    try:
        email_status = validate_email(user_invite.email, 'en')
        if email_status['score'] <= 0.60:
            user_invite.status = 'REJECTED'
            user_invite.process_status = 'ERROR'
            user_invite.process_message = 'Your email is invalid'
        user_invite.email_quality = email_status['score']
        user_invite.email_status = email_status

    except ValidationException as e:
        user_invite.status = 'REJECTED'
        user_invite.process_status = 'ERROR'
        user_invite.process_message = str(e)

    except Exception:
        raise RetryTask(f'Retrying email validation for invite {invite_id}')

    user_invite.save()

    return True


@shared_task(priority=TaskPriority.ACADEMY.value)
def async_set_gitpod_user_expiration(gitpoduser_id):
    logger.debug(f'Recalculate gitpoduser expiration for {gitpoduser_id}')
    return set_gitpod_user_expiration(gitpoduser_id) is not None


@shared_task(priority=TaskPriority.ACADEMY.value)
def async_add_to_organization(cohort_id, user_id):
    return add_to_organization(cohort_id, user_id)


@shared_task(priority=TaskPriority.ACADEMY.value)
def async_remove_from_organization(cohort_id, user_id, force=False):
    return remove_from_organization(cohort_id, user_id, force=force)


@shared_task(priority=TaskPriority.NOTIFICATION.value)
def async_accept_user_from_waiting_list(user_invite_id: int) -> None:
    from .models import UserInvite

    logger.debug(f'Process to accept UserInvite {user_invite_id}')

    if not (invite := UserInvite.objects.filter(id=user_invite_id).first()):
        logger.error(f'UserInvite {user_invite_id} not found')
        return

    if not invite.email:
        invite.status = 'ACCEPTED'
        invite.process_status = 'ERROR'
        invite.process_message = "Can't determine the user email"
        invite.save()
        return

    if user := User.objects.filter(email=invite.email).first():
        invite.status = 'ACCEPTED'
        invite.process_status = 'DONE'
        invite.process_message = f'User already exists with the id {user.id}'
        invite.save()
        return

    user = User(username=invite.email,
                email=invite.email,
                first_name=invite.first_name or '',
                last_name=invite.last_name or '')

    user.save()

    invite.user = user
    invite.status = 'ACCEPTED'
    invite.process_status = 'DONE'
    invite.process_message = f'Registered as User with id {user.id}'
    invite.save()

    notify_actions.send_email_message(
        'pick_password',
        user.email, {
            'SUBJECT': 'Set your password at 4Geeks',
            'LINK': os.getenv('API_URL', '') + f'/v1/auth/password/{invite.token}',
        },
        academy=invite.academy)


@task(priority=TaskPriority.OAUTH_CREDENTIALS.value)
def destroy_legacy_key(legacy_key_id, **_):
    from .models import LegacyKey

    LegacyKey.objects.filter(id=legacy_key_id).delete()


@task(priority=TaskPriority.STUDENT.value)
def create_user_from_invite(user_invite_id: int, **_):
    logger.info('Running create_user_from_invite task')

    if not (user_invite := UserInvite.objects.filter(id=user_invite_id).only(
            'email', 'first_name', 'last_name', 'status', 'user_id', 'token', 'academy__id').first()):
        raise RetryTask('User invite not found')

    if user_invite.status != 'ACCEPTED':
        raise AbortTask('User invite is not accepted')

    if user_invite.user or (user := User.objects.filter(email=user_invite.email).only('id').first()):
        if not user_invite.user:
            user_invite.user = user
            user_invite.save()

        raise AbortTask('User invite is already associated to a user')

    if not user_invite.email:
        raise AbortTask('No email found')

    user = User()
    user.username = user_invite.email
    user.email = user_invite.email
    user.first_name = user_invite.first_name or ''
    user.last_name = user_invite.last_name or ''
    user.save()

    if user_invite.token:
        notify_actions.send_email_message(
            'pick_password',
            user.email, {
                'SUBJECT': 'Set your password at 4Geeks',
                'LINK': os.getenv('API_URL', '') + f'/v1/auth/password/{user_invite.token}'
            },
            academy=user_invite.academy)


@task(priority=TaskPriority.REALTIME.value)
def check_credentials(user_id: int, check=None, **_):

    def error(credentials):
        credentials.health_status = {'rigobot': {'id': credentials.rigobot_id, 'status': 'NOT_FOUND'}}
        credentials.rigobot_id = None
        credentials.save()

    logger.info('Running check_credentials task')

    if check is None:
        raise AbortTask('Nothing to check')

    if not (credentials := FirstPartyCredentials.objects.filter(user__id=user_id).only(
            'health_status', 'rigobot_id', 'user__email').first()):
        raise RetryTask('FirstPartyCredentials not found')

    # maybe with a for loop it should be better
    if 'rigobot' in check:
        if credentials.rigobot_id is None:
            if 'rigobot' in credentials.health_status:
                del credentials.health_status['rigobot']
                credentials.save()

            return

        else:
            with Service('rigobot') as s:
                response = s.get(
                    f'/v1/auth/app/user/?email={credentials.user.email}&id={credentials.rigobot_id}')

                if response.status_code != 200:
                    return error(credentials)

                json = response.json()
                if not isinstance(json, list) or len(json) == 0:
                    return error(credentials)

                else:
                    credentials.health_status = {
                        'rigobot': {
                            'id': credentials.rigobot_id,
                            'status': 'HEALTHY'
                        }
                    }
                    credentials.save()


@task(priority=TaskPriority.REALTIME.value)
def import_external_user(webhook_id: int, **_):
    logger.info('Running check_credentials task')

    webhook = FirstPartyWebhookLog.objects.filter(id=webhook_id).first()
    if webhook is None:
        raise AbortTask('Webhook not found')

    if webhook.data is None or not isinstance(webhook.data, dict):
        logger.error(f'Webhook {webhook.type} requires a data field as json')
        return

    errors = []
    for field in ['id', 'email', 'first_name', 'last_name']:
        if field not in webhook.data:
            errors.append(field)

    if len(errors) > 0:
        format = ', '.join(['data.' + x for x in errors])
        logger.error(
            f'Webhook {webhook.type} requires a data field as json with the following fields: {format}')
        return

    if User.objects.filter(credentials__rigobot_id=webhook.data['id']).exists():
        return

    user = User.objects.filter(email=webhook.data['email']).first()
    if user is None:
        user = User.objects.create(email=webhook.data['email'],
                                   username=webhook.data['email'],
                                   first_name=webhook.data['first_name'],
                                   last_name=webhook.data['last_name'],
                                   is_active=True)

        FirstPartyCredentials.objects.get_or_create(user=user, rigobot_id=webhook.data['id'])
