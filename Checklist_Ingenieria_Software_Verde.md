# Lista de verificación para el desarrollo de software verde

## Matriz resumen de cumplimiento

| # | Fase | Sí | No | N/A | Total ítems | % Cumplimiento* |
|---|---|---|---|---|---|---|
| 1 | Planificación y diseño | 10 | 0 | 0 | 10 | 100% |
| 2 | Desarrollo | 10 | 0 | 1 | 11 | 100% |
| 3 | Pruebas y optimización | 4 | 0 | 0 | 4 | 100% |
| 4 | Implementación | 5 | 0 | 1 | 6 | 100% |
| 5 | Mantenimiento y supervisión | 8 | 0 | 1 | 9 | 100% |
| 6 | Participación y educación de los usuarios | 4 | 0 | 2 | 6 | 100% |
| **Total** | | **41** | **0** | **5** | **46** | **100%** |

*% Cumplimiento se calcula sobre los ítems aplicables (excluyendo N/A). En todas las fases se cumplió el 100% de los criterios evaluables.*

---

## 1. Planificación y diseño

| Pregunta | Sí | No | NA | Comentario |
|---|---|---|---|---|
| Se definieron objetivos de sostenibilidad alineados con los objetivos del proyecto. | X | | | Se definieron objetivos enfocado en minimizar la huella de carbono y el impacto energético del sistema, priorizando el uso de arquitecturas orientadas a eventos y rutinas de bajo consumo en el hardware. |
| Se consideraron los impactos ambientales del software en todas sus fases: desarrollo, operación y desecho/reúso. | X | | | Se consideró un estudio de factibilidad ambiental, abarcando la eficiencia durante el desarrollo y la operación, y estableciendo un protocolo de disposición adecuada para el recambio de sensores y microcontroladores. |
| Se evaluó el impacto medioambiental del software propuesto durante la planificación. | X | | | Durante la planificación y factibilidad se evaluó el impacto, determinando que la migración de un servidor local físico a una arquitectura cloud reduce drásticamente el consumo continuo de energía del establecimiento. |
| Se documentaron los objetivos y prácticas de sostenibilidad. | X | | | Se documentó en el punto de objetivos específicos. |
| Se dieron prioridad a los principios de diseño energéticamente eficiente desde el principio. | X | | | La arquitectura impulsada por eventos es por naturaleza altamente eficiente en consumo energético. |
| Se implementaron estándares de codificación sostenible en el desarrollo del proyecto. | X | | | Se implementaron estándares de codificación sostenible, destacando el uso de funciones asíncronas en el backend (FastAPI) para minimizar el tiempo de bloqueo de la CPU y la gestión eficiente de Wi-Fi en el ESP32 para reducir el consumo eléctrico en sitio. |
| Se consideró el impacto energético del lenguaje de programación o framework elegido para el contexto del problema. | X | | | Python con FastAPI y C++ (para el ESP32) son herramientas muy eficientes. C++ gasta mínima energía, y FastAPI procesa concurrencia sin bloquear el servidor, reduciendo el trabajo de la CPU. |
| Se seleccionó el hardware y la infraestructura teniendo en cuenta la eficiencia energética y las fuentes de energía renovables. | X | | | Se priorizó el ESP32 por su consumo en comparación con ordenadores de placa única. A nivel de nube, se seleccionaron servicios respaldados por los centros de datos de Google los cuales operan bajo compromisos públicos de carbono neutralidad y uso de energías renovables. |
| Se tomaron decisiones arquitectónicas y de código para reducir las emisiones de carbono. | X | | | La arquitectura Serverless y BaaS significa que comparte infraestructura física con otros, lo que contamina mucho menos que tener un servidor dedicado propio encendido 24/7 solo para tu estacionamiento. |
| Se incorporaron consideraciones de escalabilidad para evitar el sobre aprovisionamiento. | X | | | Al usar la nube bajo demanda, el sistema escala solo cuando entran autos. No hay "servidores inactivos" gastando luz de más; se usa exactamente lo que se necesita. |

## 2. Desarrollo

| Pregunta | Sí | No | NA | Comentario |
|---|---|---|---|---|
| Utiliza algoritmos y estructuras de datos eficientes para minimizar el uso de la CPU y la memoria. | X | | | Se utilizaron estructuras JSON ligeras para la transmisión de datos y esquemas Pydantic en FastAPI que validan la información de manera ultra rápida, minimizando la carga en la memoria RAM del servidor. |
| Se han elegido algoritmos de alto rendimiento y bajo consumo de energía. | X | | | Se utilizó el cálculo de distancia en C++ (d = t x 0.034/2), una operación que el ESP32 ejecuta en microsegundos, consumiendo mínima energía. |
| Optimiza el código para mejorar el rendimiento y reducir el tiempo de procesamiento. | X | | | La adopción de Webhooks y programación asíncrona en FastAPI permite que el código reaccione a eventos instantáneamente sin bloquear hilos de ejecución. |
| Minimizar los cálculos, bucles y consultas a bases de datos innecesarios. | X | | | El código del ESP32 incluye lógica condicional para enviar un payload a la nube solo si el estado de la plaza cambia, eliminando bucles infinitos de transmisiones repetitivas. |
| Evita el procesamiento y almacenamiento redundantes de datos que consumen energía innecesariamente. | X | | | El sistema utiliza Firebase para sobrescribir el estado en tiempo real de la plaza (evitando crear miles de registros históricos inútiles mientras un auto está estacionado) y reserva a Supabase estrictamente para almacenar el registro único y final de cada ticket de pago. |
| El diseño incluye estrategias para reducir la cantidad de datos que se procesan, transfieren y almacenan (por ejemplo, compresión, paginación en APIs). | X | | | Los payloads JSON están comprimidos a solo dos claves (slot_id y status), y el historial web usa un algoritmo de agrupación jerárquica para estructurar la visualización. |
| Implementa la carga diferida y la recuperación de datos bajo demanda cuando sea apropiado. | X | | | El módulo de Historial Vehicular en el dashboard solo hace consultas a la base de datos (Firebase/Supabase) cuando el operario ejecuta explícitamente una búsqueda (recuperación bajo demanda). |
| Se detienen las tareas que no son necesarias. | X | | | La arquitectura Serverless de Vercel y el escenario de Make entran en modo reposo absoluto y no consumen CPU cuando no hay actividad de vehículos o pagos. |
| Se deshabilitan las notificaciones. | X | | | Se deshabilitaron alertas innecesarias. El flujo automatizado está programado para disparar un mensaje de WhatsApp única y exclusivamente cuando un pago ha sido concretado y verificado. |
| Se deshabilita el hardware no utilizado durante las mediciones o cuando no se requieren. | X | | | La lógica de control del hardware apaga (corta la energía del relé) la luz LED indicadora cuando la plaza está ocupada, ahorrando consumo eléctrico por cada vehículo estacionado. |
| Se aprovecha la aceleración del hardware (por ejemplo, GPU, TPU) de manera eficiente. | | | X | No requieren renderizado gráfico ni inferencia de IA/Machine Learning, por lo que usar GPU/TPU sería un desperdicio energético. |

## 3. Pruebas y optimización

| Pregunta | Sí | No | NA | Comentario |
|---|---|---|---|---|
| Se midió el consumo energético del código durante el desarrollo. | X | | | Se utilizaron las métricas de transferencia de datos (ej. 3.6 KB) y el tiempo de ejecución (milisegundos) en los logs de la plataforma de integración (Make) y el servidor (Vercel). |
| Se utilizaron herramientas de perfilado para identificar y optimizar los procesos que consumen mucha energía. | X | | | Se utilizaron las herramientas de monitorización de "History" para identificar cuellos de botella y exceso de procesamiento computacional originado por notificaciones irrelevantes. |
| Se refactorizó el código para mejorar la eficiencia. | X | | | Se refactorizó la lógica de comunicación del sistema, reemplazando el modelo de consulta constante al servidor por una arquitectura basada en eventos. Asimismo, se optimizó el firmware del ESP32 para que solo transmita datos cuando existe un cambio físico real en la plaza. |
| Se simularon cargas de trabajo para garantizar un rendimiento energéticamente eficiente a escala. | X | | | Se realizaron pruebas controladas simulando ráfagas de notificaciones y múltiples ciclos de estacionamiento, validando que el sistema procesa la carga en colas ordenadas sin sobresaturar el uso de CPU. |

## 4. Implementación

| Pregunta | Sí | No | NA | Comentario |
|---|---|---|---|---|
| Se eligieron proveedores de servicios en la nube comprometidos con las energías renovables. | X | | | Los servicios base (Firebase, Supabase y Vercel) están alojados sobre la infraestructura de Google Cloud y AWS, empresas que cuentan con compromisos públicos para operar con energía 100% renovable y alcanzar la neutralidad de carbono. |
| Se implementaron arquitecturas sin servidor o con auto escalado para ajustar el uso de recursos a la demanda. | X | | | El frontend y la pasarela de pagos están desplegados en Vercel (plataforma Serverless), mientras que Firebase y Supabase operan como Backend-as-a-Service (BaaS), escalando sus recursos automáticamente solo cuando el estacionamiento tiene actividad. |
| Se optimizaron las configuraciones de implementación para minimizar la asignación de recursos. | X | | | El sistema no tiene servidores inactivos (idle) consumiendo RAM o CPU de manera permanente; los recursos se asignan y liberan en cuestión de milisegundos por cada petición. |
| Se minimizó la transferencia de datos a través de la red. | X | | | La implementación minimiza el uso de la red enviando micro-cargas útiles (payloads JSON) desde el ESP32 y utilizando webhooks que evitan el tráfico de red redundante hacia la API de Mercado Pago. |
| Se evaluó la posibilidad de consolidar aplicaciones y optimizar el tamaño de los centros de datos (en caso de no usar la nube). | | | X | Todo el ecosistema del proyecto está nativamente diseñado y desplegado 100% en la nube, por lo que no se administran centros de datos físicos locales. |
| Se implementó una programación consciente del consumo energético (por ejemplo, equilibrio de carga consciente de las emisiones de carbono). | X | | | Se aplicó el principio de despliegue consciente de emisiones (Carbon-Aware) configurando las instancias en regiones de centros de datos geográficamente ubicadas en zonas con baja intensidad de carbono en su red eléctrica. |

## 5. Mantenimiento y supervisión

| Pregunta | Sí | No | NA | Comentario |
|---|---|---|---|---|
| Se supervisa periódicamente el consumo energético y la huella de carbono del software para identificar áreas de mejora. | X | | | Se ha establecido un protocolo de mantenimiento donde se evaluarán los paneles de uso de Vercel y Make (Data Transfer). Si se detectan picos anómalos de transferencia de datos, se programará una refactorización de los payloads JSON o de las consultas a Supabase para mantener la eficiencia energética. |
| La aplicación adapta su comportamiento en función del modo de energía del dispositivo o de las condiciones operativas. | X | | | Se utilizará el modo oscuro para cuando aparte su comportamiento en función del dispositivo. |
| Se utiliza, cuando es posible, electricidad de baja intensidad de carbono para alimentar los servidores. | X | | | Tal como se justificó en la fase de implementación, la VPS Contabo y la infraestructura en la nube operan bajo políticas de energía limpia y fuentes verdes. |
| Se utilizan fuentes de energía renovable para alimentar servidores y dispositivos. | X | | | Servidor Cloud: Contabo utiliza 100% energía renovable certificada. Dispositivos IoT utilizados (ESP32, Sensores y relés). |
| Se aprovechan las herramientas del proveedor para medir el impacto. | X | | | Se aprovechan los paneles nativos de Vercel (Analytics) y Make que mide la transferencia en KB como indicadores indirectos del esfuerzo computacional. |
| Se recopilan los comentarios de los usuarios sobre el rendimiento y la eficiencia. | | | X | Actualmente no se cuenta con una fase de producción que permita recopilar retroalimentación o comentarios relevante sobre la eficiencia del software. |
| Se actualizan y optimizan los algoritmos y la infraestructura basándose en los datos de supervisión. | X | | | Se estableció ciclos de revisión donde se analizan las métricas de transferencia en la nube para programar la refactorización y optimización continua de los algoritmos y payloads JSON. |
| Se considera cómo prolongar la vida útil de los dispositivos a través de cambios en el código o en las especificaciones. | X | | | La lógica implementada en C++ de enviar datos solo cuando hay cambios de estado evita el sobrecalentamiento y prolonga la vida útil del ESP32. |
| Se mantiene la documentación sobre prácticas ecológicas y actualizaciones. | X | | | La documentación técnica del proyecto (informe final) mantiene referencias dedicadas a justificar la arquitectura desde una perspectiva de "Green Software". |

## 6. Participación y educación de los usuarios

| Pregunta | Sí | No | NA | Comentario |
|---|---|---|---|---|
| Se educó a los usuarios sobre prácticas de uso sostenible. | X | | | Se incluyó un manual de capacitación del sistema sobre cómo el uso adecuado del panel web ayuda a minimizar peticiones al servidor y ahorrar energía. Se abarca lo que es prácticas de uso sostenible del sistema, interpretación del sistema de estacionamiento y dashboard web, roles y responsabilidades de cada usuario. Adicionalmente se capacitó a los usuarios y se grabó un video tutorial explicativo acerca del funcionamiento del sistema. |
| Se diseñaron interfaces que promuevan comportamientos eficientes desde el punto de vista energético. | X | | | El dashboard web se diseñó bajo un enfoque minimalista y de carga rápida, reduciendo el tiempo en pantalla ("screen-on time") necesario para que el operario visualice el estado de las plazas. Se aplicó el modo oscuro y accesibilidad. |
| Se fomentan los comentarios sobre el rendimiento y la sostenibilidad del software. | X | | | Al ser una herramienta operativa interna para personal de caseta y administrador, el feedback se centra en la usabilidad. |
| Se realiza un seguimiento de las mejoras en la eficiencia energética a lo largo del tiempo. | X | | | Se ha programado el rastreo del consumo de transferencia de datos en Make y Vercel a lo largo de los ciclos de uso del sistema. |
| Se informa sobre el impacto medioambiental de conformidad con las normas o certificaciones pertinentes. | | | X | El proyecto tiene un enfoque académico y técnico, por lo que no se encuentra sujeto a normativas oficiales de reporte de huella de carbono exigidas a grandes corporaciones. |
| Se considera una estrategia global de software verde que involucre a la empresa, incluyendo acuerdos de compra de energía o tarifas verdes. | | | X | La negociación de tarifas verdes o acuerdos corporativos de energía escapa al alcance técnico y a las competencias de este proyecto de desarrollo de software. |

## Conclusiones y/o comentarios generales

La transición de un modelo de comunicación tradicional (basado en consultas constantes) hacia una arquitectura orientada a eventos (Webhooks y lógica de cambio de estado en el ESP32) demuestra que la eficiencia energética es un subproducto natural de un buen diseño de software. Al eliminar el procesamiento y la transmisión de datos redundantes, el sistema minimiza el consumo de CPU en la nube y el uso de radiofrecuencia en el hardware, cumpliendo con los estándares de diseño energéticamente eficiente desde la fase de planificación.

La aplicación de la lista de verificación de software verde evidencia que la sostenibilidad no es una característica aislada, sino una metodología que mejora la calidad técnica integral del proyecto. Al considerar el ciclo de vida del software y establecer un plan de mantenimiento continuo basado en métricas de supervisión, el proyecto asegura su eficiencia operativa a largo plazo y reduce el desperdicio de recursos, convirtiéndose en un modelo de desarrollo responsable y escalable.
