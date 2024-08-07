# https://www.eventbrite.com.mx/platform/api#/reference/event/retrieve-an-event?console=1
# '%2C' = ','
EVENTBRITE_EVENTS_URL = (
    "https://www.eventbriteapi.com/v3/organizations/:id/events/?" "expand=organizer%2Cvenue&status=live"
)
EVENTBRITE_EVENTS = {
    "pagination": {"object_count": 1, "page_number": 1, "page_size": 50, "page_count": 1, "has_more_items": False},
    "events": [
        {
            "name": {
                "text": "GEEKTALKS - PRESENTACIÓN DE PROYECTOS FINALES",
                "html": "GEEKTALKS - PRESENTACIÓN DE PROYECTOS FINALES",
            },
            "description": {
                "text": "GEEKTALKS - DEMO DAY ¡TÚ TAMBIÉN HARÁS ESTO CUANDO SEAS PROGRAMADOR!",
                "html": "GEEKTALKS - DEMO DAY ¡TÚ TAMBIÉN HARÁS ESTO CUANDO SEAS PROGRAMADOR!",
            },
            "url": "https://www.eventbrite.com/e/geektalks-presentacion-de-proyectos-finales-tickets-1",
            "start": {"timezone": "Europe/Madrid", "local": "2021-12-01T18:30:00", "utc": "2021-12-01T17:30:00Z"},
            "end": {"timezone": "Europe/Madrid", "local": "2021-12-01T19:30:00", "utc": "2021-12-01T18:30:00Z"},
            "organization_id": "1",
            "created": "2021-11-19T03:24:52Z",
            "changed": "2021-11-19T04:27:58Z",
            "published": "2021-11-19T04:27:58Z",
            "capacity": 200,
            "capacity_is_custom": False,
            "status": "live",
            "currency": "USD",
            "listed": True,
            "shareable": True,
            "invite_only": False,
            "online_event": True,
            "show_remaining": False,
            "tx_time_limit": 480,
            "hide_start_date": False,
            "hide_end_date": False,
            "locale": "en_US",
            "is_locked": False,
            "privacy_setting": "unlocked",
            "is_series": False,
            "is_series_parent": False,
            "inventory_type": "limited",
            "is_reserved_seating": False,
            "show_pick_a_seat": False,
            "show_seatmap_thumbnail": False,
            "show_colors_in_seatmap_thumbnail": False,
            "source": "coyote",
            "is_free": True,
            "version": None,
            "summary": "GEEKTALKS - DEMO DAY ¡TÚ TAMBIÉN HARÁS ESTO CUANDO SEAS PROGRAMADOR!",
            "facebook_event_id": "1",
            "logo_id": "1",
            "organizer_id": "1",
            "venue_id": "1",
            "category_id": "1",
            "subcategory_id": "1",
            "format_id": "1",
            "id": "1",
            "resource_uri": "https://www.eventbriteapi.com/v3/events/1/",
            "is_externally_ticketed": False,
            "logo": {
                "crop_mask": {"top_left": {"x": 0, "y": 0}, "width": 2160, "height": 1080},
                "original": {
                    "url": "https://img.evbuc.com/https%3A%2F%2Fcdn.evbuc.com%2Fimages%2F1%2F187450375408%2F1%2Foriginal.20211119-035031?auto=format%2Ccompress&q=75&sharp=10&s=683defa0f95ab0fab375d93d30fd83f2",
                    "width": 2160,
                    "height": 1080,
                },
                "id": "1",
                "url": "https://img.evbuc.com/https%3A%2F%2Fcdn.evbuc.com%2Fimages%2F1%2F187450375408%2F1%2Foriginal.20211119-035031?h=200&w=450&auto=format%2Ccompress&q=75&sharp=10&rect=0%2C0%2C2160%2C1080&s=40991174ed57f5f54596a762c94eb850",
                "aspect_ratio": "2",
                "edge_color": "#fcfcfc",
                "edge_color_set": True,
            },
            "organizer": {
                "description": {
                    "text": "4Geeks Academy somos un Bootcamp de programación con más de seis campus en España, Estados Unidos, Chile y Venezuela. Estamos enfocados en desarrollar las habilidades necesarias para convertirte en un programador de software completo y exitoso. Contamos con más de 600 graduados, ¡el 90% ya está trabajando como programador!\r\nTenemos dos tipos de programas Part-Time y Full-Time. En cada una de ellos, recibirás la mejor atención posible, nuestras clases son personalizadas (en promedio 1 profesor cada 5 estudiantes). Recibirás asesoramiento en todo momento a través de nuestras mentorías uno a uno y soporte online y offline, incluso después de que consigas trabajo. Además, nos encargaremos de ayudarte a conseguir trabajo, te asesoraremos en la construcción de tu CV, construcción de tu portfolio, entre otros, también te prepararemos para entrevistas de manera personalizada (según el puesto al que estés aplicando) para que seas el candidato perfecto para las empresas.  \r\n ",
                    "html": "<p>4Geeks Academy somos un Bootcamp de programación con más de seis campus en España, Estados Unidos, Chile y Venezuela. Estamos enfocados en desarrollar las habilidades necesarias para convertirte en un programador de software completo y exitoso. Contamos con más de 600 graduados, ¡el 90% ya está trabajando como programador!</p>\r\n<p>Tenemos dos tipos de programas Part-Time y Full-Time. En cada una de ellos, recibirás la mejor atención posible, nuestras clases son personalizadas (en promedio 1 profesor cada 5 estudiantes). Recibirás asesoramiento en todo momento a través de nuestras mentorías uno a uno y soporte online y offline, incluso después de que consigas trabajo. Además, nos encargaremos de ayudarte a conseguir trabajo, te asesoraremos en la construcción de tu CV, construcción de tu portfolio, entre otros, también te prepararemos para entrevistas de manera personalizada (según el puesto al que estés aplicando) para que seas el candidato perfecto para las empresas.  </p>\r\n<p> </p>",
                },
                "long_description": {
                    "text": "4Geeks Academy somos un Bootcamp de programación con más de seis campus en España, Estados Unidos, Chile y Venezuela. Estamos enfocados en desarrollar las habilidades necesarias para convertirte en un programador de software completo y exitoso. Contamos con más de 600 graduados, ¡el 90% ya está trabajando como programador!\r\nTenemos dos tipos de programas Part-Time y Full-Time. En cada una de ellos, recibirás la mejor atención posible, nuestras clases son personalizadas (en promedio 1 profesor cada 5 estudiantes). Recibirás asesoramiento en todo momento a través de nuestras mentorías uno a uno y soporte online y offline, incluso después de que consigas trabajo. Además, nos encargaremos de ayudarte a conseguir trabajo, te asesoraremos en la construcción de tu CV, construcción de tu portfolio, entre otros, también te prepararemos para entrevistas de manera personalizada (según el puesto al que estés aplicando) para que seas el candidato perfecto para las empresas.  \r\n ",
                    "html": "<p>4Geeks Academy somos un Bootcamp de programación con más de seis campus en España, Estados Unidos, Chile y Venezuela. Estamos enfocados en desarrollar las habilidades necesarias para convertirte en un programador de software completo y exitoso. Contamos con más de 600 graduados, ¡el 90% ya está trabajando como programador!</p>\r\n<p>Tenemos dos tipos de programas Part-Time y Full-Time. En cada una de ellos, recibirás la mejor atención posible, nuestras clases son personalizadas (en promedio 1 profesor cada 5 estudiantes). Recibirás asesoramiento en todo momento a través de nuestras mentorías uno a uno y soporte online y offline, incluso después de que consigas trabajo. Además, nos encargaremos de ayudarte a conseguir trabajo, te asesoraremos en la construcción de tu CV, construcción de tu portfolio, entre otros, también te prepararemos para entrevistas de manera personalizada (según el puesto al que estés aplicando) para que seas el candidato perfecto para las empresas.  </p>\r\n<p> </p>",
                },
                "resource_uri": "https://www.eventbriteapi.com/v3/organizers/1/",
                "_type": "organizer",
                "id": "1",
                "name": "4Geeks Academy España",
                "url": "https://www.eventbrite.com/o/4geeks-academy-espana-1",
                "num_past_events": 41,
                "num_future_events": 1,
                "twitter": "@4geeksacademyes",
                "facebook": "4geeksacademyes",
                "instagram": "23558070851",
                "organization_id": "1",
                "disable_marketing_opt_in": False,
                "logo_id": "1",
            },
            "venue": {  # TODO: check this section
                "address": {
                    "address_1": "11200 Southwest 8th Street",
                    "address_2": "",
                    "city": "Miami",
                    "region": "FL",
                    "postal_code": "33174",
                    "country": "US",
                    "latitude": "25.7580596",
                    "longitude": "-80.37702200000001",
                    "localized_address_display": "11200 Southwest 8th Street, Miami, FL 33174",
                    "localized_area_display": "Miami, FL",
                    "localized_multi_line_address_display": ["11200 Southwest 8th Street", "Miami, FL 33174"],
                },
                "resource_uri": "https://www.eventbriteapi.com/v3/venues/1/",
                "id": "1",
                "age_restriction": None,
                "capacity": None,
                "name": "Florida International University College of Business",
                "latitude": "25.7580596",
                "longitude": "-80.37702200000001",
            },
        }
    ],
}


def get_eventbrite_events_url(id: str):
    return EVENTBRITE_EVENTS_URL.replace(":id", id)
