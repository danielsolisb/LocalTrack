# LocalTrack
LocalTrack es el sistema local desarrollado en Python utilizando Flask, diseñado para funcionar en una Raspberry Pi como complemento del sistema en la nube FlowTrack. Su propósito principal es procesar y gestionar el conteo vehicular en tiempo real a partir de múltiples cámaras instaladas en intersecciones específicas, permitiendo además la configuración personalizada de variables para análisis y cálculos avanzados.

# Características principales:
Interfaz web ligera: Proporciona una plataforma de configuración y monitoreo accesible desde cualquier navegador conectado a la red local.
Autenticación de usuarios: Acceso seguro mediante login integrado con Flask-Login.
Procesamiento en tiempo real: Manejo constante de datos vehiculares capturados por las cámaras conectadas.
Comunicación con FlowTrack: Envío de datos y configuraciones al sistema principal en la nube, utilizando protocolos eficientes como MQTT o REST APIs.
Escalabilidad modular: Estructura modular para facilitar futuras ampliaciones y personalizaciones.
# Tecnologías utilizadas:
Python: Lenguaje base del sistema.
Flask: Framework web para el desarrollo de la interfaz y API local.
SQLite: Base de datos ligera para almacenar configuraciones y datos intermedios.
Raspberry Pi: Hardware de procesamiento y ejecución local.
Protocolo MQTT (opcional): Para comunicación en tiempo real con FlowTrack.
# Casos de uso:
Configuración de variables específicas para el análisis del tráfico vehicular.
Supervisión y validación de datos recopilados antes de enviarlos al sistema FlowTrack.
Funcionalidad independiente para monitoreo local sin conexión a la nube.
LocalTrack es el núcleo operativo local que asegura un procesamiento rápido y eficiente en el sitio, optimizando la integración con FlowTrack para una solución completa de gestión vehicular.


localtrack/
├── app/
│   ├── __init__.py      # Inicializa la app Flask
│   ├── models.py        # Modelos de base de datos
│   ├── routes.py        # Rutas principales
│   ├── forms.py         # Formularios Flask-WTF
│   ├── templates/       # Plantillas HTML
│   │   ├── base.html    # Plantilla base
│   │   ├── login.html   # Página de login
│   │   ├── dashboard.html # Página de configuración
│   └── static/          # Archivos estáticos (CSS, JS, imágenes)
│       ├── css/
│       ├── js/
│       └── img/
├── migrations/          # Archivos de migraciones (creados automáticamente)
├── venv/                # Entorno virtual (Python virtualenv)
├── config.py            # Configuración del proyecto
├── requirements.txt     # Dependencias del proyecto
└── run.py               # Punto de entrada de la aplicación
