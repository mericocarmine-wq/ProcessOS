# ADR-010 — Búsqueda geográfica acotada y límites de disponibilidad

Fecha: 2026-09-15
Estado: mitigación implementada; disponibilidad independiente pendiente de decisión.

## Causa comprobada

La consulta anterior resolvía áreas administrativas globales por nombre antes de
buscar empresas. Se observaron tanto HTTP 504 como HTTP 200 con `elements: []` y
un `remark` de timeout. Ese último caso no es una búsqueda vacía correcta.
Los servidores públicos alternativos también agotaron el tiempo de conexión.

## Decisión

- Resolver primero el nodo de localidad y consultar después un rectángulo de
  aproximadamente 10 × 10 km. No representa el límite administrativo municipal.
- Mantener los filtros de sector y la trazabilidad de OSM; conservar teléfono,
  correo y web cuando están publicados, sin inventar contactos ausentes.
- Admitir coordenadas para mover el centro. Los nombres son exactos; ciudades
  tienen prioridad sobre pueblos y aldeas. Homónimos del mismo nivel requieren
  coordenadas. Se excluyen regiones polares y cercanas al antimeridiano.
- Consultar primero overpass-api.de y solo después un servidor alternativo,
  sin lanzar la misma consulta simultáneamente contra tres servidores públicos.
- Limitar a 8 segundos el tiempo solicitado al servidor, 12 por petición HTTP y
  35 para el conjunto de descubrimiento. La escritura en BD sucede después.
- Reutilizar respuestas válidas durante 10 minutos en una caché de proceso de
  hasta 128 entradas, separada por configuración de endpoints y consulta. No
  contiene datos internos de organizaciones; no persiste entre reinicios y no
  sirve datos caducados. No se cachean errores de transporte/formato ni `remark`.
- Distinguir en UI resultados, duplicados, falta de cobertura, error del proveedor
  y error de conexión. No afirmar que una zona no tiene empresas cuando OSM no
  las contiene. Un timeout del navegador no acredita que la operación no acabó:
  se indica revisar los procesos antes de repetir.

Referencia de la sintaxis y límites:
[Overpass QL](https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL).

## Verificación y límites pendientes

La consulta real `construction / Madrid / 5` devolvió cinco registros en 10,79 s
y se repitió desde caché sin nueva petición. Entre ellos, Lozano López
Saneamientos incluía teléfono y web. No se generaron registros ficticios.

Una prueba posterior mediante el BFF del CRM recibió un 504 del servidor
principal y timeout del alternativo, correctamente traducidos a 503. La cuenta
y organización temporales de esa prueba se eliminaron, sin modificar los datos
comerciales existentes. **Esto impide afirmar disponibilidad definitiva**:
la mitigación no transforma un servicio público en una fuente garantizada.

Pruebas automatizadas cubren consultas acotadas, conservación de contactos,
caché entre instancias, fallback, HTTP 200 fallido, localidad desconocida o
ambigua, coordenadas inválidas, cancelación y estados del formulario.

Para eliminar esta dependencia hace falta elegir una fuente comercial de
empresas/contactos con cuenta y condiciones acordadas, o una base propia de
datos abiertos con importación, almacenamiento y actualizaciones. Ninguna de
esas ampliaciones se ha contratado ni desplegado sin decisión del usuario.
Este cambio tampoco implementa extracción de contactos desde páginas web ni
un worker durable; no cierra por sí solo toda la fase de Discovery & Research.
