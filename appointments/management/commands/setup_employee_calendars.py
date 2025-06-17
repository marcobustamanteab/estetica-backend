from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from services.google_calendar_service import GoogleCalendarService
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Crear calendarios de Google para todos los empleados activos'
    
    def add_arguments(self, parser):
        # Argumentos opcionales para el comando
        parser.add_argument(
            '--employee-id',
            type=int,
            help='Crear calendario solo para un empleado específico (por ID)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar creación de calendario incluso si ya tiene uno',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué empleados necesitan calendario sin crearlos',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando configuración de calendarios de empleados...')
        )
        
        try:
            # Verificar configuración de Google Calendar
            calendar_service = GoogleCalendarService()
            self.stdout.write("✅ Servicio de Google Calendar configurado correctamente")
            
        except Exception as e:
            raise CommandError(f'❌ Error configurando Google Calendar: {e}')
        
        # Determinar qué empleados procesar
        employees = self.get_employees_to_process(options)
        
        if not employees.exists():
            self.stdout.write(
                self.style.WARNING('⚠️ No hay empleados para procesar')
            )
            return
        
        # Mostrar resumen
        self.show_summary(employees, options)
        
        # Procesar empleados
        if not options['dry_run']:
            self.process_employees(employees, calendar_service, options)
        else:
            self.stdout.write(
                self.style.WARNING('🔍 Modo dry-run: No se crearon calendarios')
            )
    
    def get_employees_to_process(self, options):
        """Obtener lista de empleados a procesar"""
        
        if options['employee_id']:
            # Procesar solo un empleado específico
            try:
                employee = User.objects.get(id=options['employee_id'])
                self.stdout.write(f"🎯 Procesando empleado específico: {employee.get_full_name()}")
                return User.objects.filter(id=options['employee_id'])
            except User.DoesNotExist:
                raise CommandError(f'❌ Empleado con ID {options["employee_id"]} no encontrado')
        
        # Obtener empleados que necesitan calendario
        if options['force']:
            # Forzar: todos los empleados activos con grupos
            employees = User.objects.filter(
                is_active=True,
                groups__isnull=False
            ).distinct()
        else:
            # Normal: solo empleados sin calendario
            employees = User.objects.filter(
                is_active=True,
                groups__isnull=False,
                google_calendar_id__isnull=True
            ).distinct()
        
        return employees
    
    def show_summary(self, employees, options):
        """Mostrar resumen de empleados a procesar"""
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 RESUMEN DE EMPLEADOS")
        self.stdout.write("="*50)
        
        for employee in employees:
            status = "🆕 Nuevo" if not employee.google_calendar_id else "🔄 Actualizar"
            groups = ", ".join([group.name for group in employee.groups.all()])
            
            self.stdout.write(
                f"{status} {employee.get_full_name()}"
            )
            self.stdout.write(f"   📧 Email: {employee.email}")
            self.stdout.write(f"   👥 Grupos: {groups}")
            if employee.google_calendar_id:
                self.stdout.write(f"   📅 Calendar ID actual: {employee.google_calendar_id}")
            self.stdout.write("")
        
        self.stdout.write(f"📝 Total de empleados: {employees.count()}")
        
        if not options['dry_run']:
            self.stdout.write("\n⏳ Iniciando creación de calendarios...")
        
        self.stdout.write("="*50 + "\n")
    
    def process_employees(self, employees, calendar_service, options):
        """Procesar empleados y crear calendarios"""
        
        success_count = 0
        error_count = 0
        
        for employee in employees:
            self.stdout.write(f"🔄 Procesando: {employee.get_full_name()}...")
            
            try:
                # Verificar si ya tiene calendario y no es forzado
                if employee.google_calendar_id and not options['force']:
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠️ Ya tiene calendario. Use --force para recrear")
                    )
                    continue
                
                # Crear calendario
                calendar_id = calendar_service.create_employee_calendar(
                    employee.get_full_name(),
                    employee.email
                )
                
                if calendar_id:
                    # Guardar ID del calendario
                    employee.google_calendar_id = calendar_id
                    employee.save(update_fields=['google_calendar_id'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Calendario creado exitosamente")
                    )
                    self.stdout.write(f"   📅 Calendar ID: {calendar_id}")
                    success_count += 1
                    
                else:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error: No se pudo crear el calendario")
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error procesando {employee.get_full_name()}: {e}")
                )
                error_count += 1
            
            self.stdout.write("")  # Línea en blanco
        
        # Mostrar resumen final
        self.show_final_summary(success_count, error_count)
    
    def show_final_summary(self, success_count, error_count):
        """Mostrar resumen final de la operación"""
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 RESUMEN FINAL")
        self.stdout.write("="*50)
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Calendarios creados exitosamente: {success_count}")
            )
        
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f"❌ Errores encontrados: {error_count}")
            )
        
        if success_count == 0 and error_count == 0:
            self.stdout.write(
                self.style.WARNING("ℹ️ No se procesaron empleados")
            )
        
        self.stdout.write("="*50)
        
        if success_count > 0:
            self.stdout.write("\n🎉 ¡Configuración completada!")
            self.stdout.write("Los empleados ahora pueden ver sus calendarios en Google Calendar")
            self.stdout.write("Las nuevas citas se sincronizarán automáticamente")
        
        if error_count > 0:
            self.stdout.write(f"\n⚠️ Revisa los errores arriba y vuelve a ejecutar para los empleados que fallaron")
            self.stdout.write("Puedes usar --employee-id <ID> para procesar empleados específicos")