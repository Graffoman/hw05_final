import datetime as dt

from django.urls import reverse


def year(request):
    current_year = dt.datetime.now().year
    return {'year': current_year}


def head_button_names(request):
    if request.path == reverse('new_post'):
        head_name = 'Добавить запись'
        button_name = 'Добавить'
        return {'head_name': head_name, 'button_name': button_name}

    if '/edit/' in request.path:
        head_name = 'Редактировать запись'
        button_name = 'Сохранить'
        return {'head_name': head_name, 'button_name': button_name}
    else:
        return {'head_name': 'head_name', 'button_name': 'button_name'}
