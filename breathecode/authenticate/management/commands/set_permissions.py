from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
import itertools

CONTENT_TYPE_PROPS = {
    'app_label': 'breathecode',
    'model': 'SortingHat',  # the team of django use models name in lower case, use upper case instead
}

# examples permissions autogenerated by django
# {'name': 'Can add cohort', 'codename': 'add_cohort'}
# {'name': 'Can change cohort', 'codename': 'change_cohort'}
# {'name': 'Can delete cohort', 'codename': 'delete_cohort'}
# {'name': 'Can view cohort', 'codename': 'view_cohort'}

PERMISSIONS = [
    {
        'name': 'Get my profile',
        'description': 'Get my profile',
        'codename': 'get_my_profile',
    },
    {
        'name': 'Create my profile',
        'description': 'Create my profile',
        'codename': 'create_my_profile',
    },
    {
        'name': 'Update my profile',
        'description': 'Update my profile',
        'codename': 'update_my_profile',
    },
    {
        'name': 'Get my certificate',
        'description': 'Get my certificate',
        'codename': 'get_my_certificate',
    },
    {
        'name': 'Get my mentoring sessions',
        'description': 'Get my mentoring sessions',
        'codename': 'get_my_mentoring_sessions',
    },
    {
        'name': 'Join mentorship',
        'description': 'Join mentorship',
        'codename': 'join_mentorship',
    },
    {
        'name': 'Join live class',
        'description': 'Join live class',
        'codename': 'live_class_join',
    },
    {
        'name': 'Join event',
        'description': 'Join event',
        'codename': 'event_join',
    },
    {
        'name': 'Get my containers',
        'description': 'Get provisioning containers',
        'codename': 'get_containers',
    },
    {
        'name': 'Add code reviews',
        'description': 'Add code reviews',
        'codename': 'add_code_review',
    },
    {
        'name': 'Upload provisioning activity',
        'description': 'Upload provisioning activity',
        'codename': 'upload_provisioning_activity',
    },
]

GROUPS = [
    {
        'name': 'Admin',
        'permissions': [x['codename'] for x in PERMISSIONS],
        'inherit': []
    },
    {
        'name': 'Default',
        'permissions': ['get_my_profile', 'create_my_profile', 'update_my_profile'],
        'inherit': []
    },
    {
        'name': 'Student',
        'permissions': ['get_my_certificate', 'get_containers', 'get_my_mentoring_sessions'],
        'inherit': []
    },
    {
        'name': 'Teacher',
        'permissions': ['add_code_review'],
        'inherit': []
    },
    {
        'name': 'Mentor',
        'permissions': ['join_mentorship', 'get_my_mentoring_sessions'],
        'inherit': []
    },
    {
        'name': 'Mentorships',
        'permissions': ['join_mentorship', 'get_my_mentoring_sessions'],
        'inherit': []
    },
    {
        'name': 'Events',
        'permissions': ['event_join'],
        'inherit': []
    },
    {
        'name': 'Classes',
        'permissions': ['live_class_join'],
        'inherit': []
    },
    {
        'name': 'Legacy',
        'permissions': [],
        'inherit': ['Classes', 'Events', 'Mentorships']
    },
]


# this function is used to can mock the list of permissions
def get_permissions():
    # prevent edit the constant
    return PERMISSIONS.copy()


# this function is used to can mock the list of groups
def get_groups():
    # prevent edit the constant
    return GROUPS.copy()


class Command(BaseCommand):
    help = 'Create default system capabilities'

    def handle(self, *args, **options):
        content_type = ContentType.objects.filter(**CONTENT_TYPE_PROPS).first()
        if not content_type:
            content_type = ContentType(**CONTENT_TYPE_PROPS)
            content_type.save()

        # reset the permissions
        Permission.objects.filter(content_type=content_type).delete()

        permissions = get_permissions()
        groups = get_groups()

        permission_instances = {}
        for permission in permissions:
            # it can use a django permissions
            instance = Permission.objects.filter(codename=permission['codename']).first()

            # it can create their own permissions
            if not instance:
                instance = Permission(name=permission['name'],
                                      codename=permission['codename'],
                                      content_type=content_type)
                instance.save()

            permission_instances[permission['codename']] = instance

        for group in groups:
            instance = Group.objects.filter(name=group['name']).first()

            # reset permissions
            if instance:
                instance.permissions.clear()

            else:
                instance = Group(name=group['name'])
                instance.save()

            # the admin have all the permissions
            if group['name'] == 'Admin':
                instance.permissions.set(Permission.objects.filter().exclude(content_type=content_type))

            permissions = list(
                itertools.chain.from_iterable(
                    [group['permissions']] +
                    [x['permissions'] for x in groups if x['name'] in group['inherit']]))

            for permission in permissions:
                instance.permissions.add(permission_instances[permission])
