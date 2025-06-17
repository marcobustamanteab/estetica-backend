
Para crear calendario por cliente en Docker-compose:

ejecutar primero 
docker-compose logs web -f

añadir a un nuevo trabajador: 
docker-compose exec web python manage.py setup_employee_calendars

para forzar recreación: 
docker-compose exec web python manage.py setup_employee_calendars --force

para un empleado específico: 
docker-compose exec web python manage.py setup_employee_calendars --employee-id 5

