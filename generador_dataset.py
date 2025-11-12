import pandas as pd
import json
import random

# --- 1. Plantillas de SQL (¡FORMATO NUEVO!) ---
# Las plantillas de TABLAS ahora tienen 3 partes:
# (pregunta_base, sql_ancho, [lista_de_columnas_disponibles])
# Las plantillas de VALOR uNICO (como SUM) se quedan igual (pregunta_base, sql)
TEMPLATES = [
    # --- GANANCIAS (PROFIT) - (Valor unico) ---
    (
        "Ganancias de hoy",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_total FROM detalle_venta dv JOIN venta v ON dv.venta_id = v.id JOIN prod_variante pv ON dv.prod_variante_id = pv.id WHERE DATE(v.fecha_venta) = DATE('now');"
    ),
    (
        "ganancias de la categoria {categoria}",
        "WITH RECURSIVE categorias_recursivas(id) AS ( SELECT id FROM categoria WHERE nombre = '{categoria}' UNION SELECT c.id FROM categoria c JOIN categorias_recursivas cr ON c.padre_id = cr.id ) SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_categoria FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id WHERE p.categoria_id IN (SELECT id FROM categorias_recursivas);"
    ),
    (
        "ganancias de la talla {talla}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_talla FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN talla t ON pv.id_talla = t.id WHERE t.talla = '{talla}';"
    ),
    (
        "ganancias del color {color}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_color FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN color c ON pv.id_color = c.id WHERE c.nombre = '{color}';"
    ),
    (
        "ganancias de la marca {marca}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_marca FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE b.nombre = '{marca}';"
    ),
    (
        "ganancias del modelo {modelo}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_modelo FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id WHERE m.nombre = '{modelo}';"
    ),
    (
        "ganancias del material {material}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_material FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN material ma ON p.material_id = ma.id WHERE ma.nombre = '{material}';"
    ),
    (
        "ganancias de la etiqueta {etiqueta}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_etiqueta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN producto_etiqueta pe ON p.id = pe.producto_id JOIN etiqueta e ON pe.etiqueta_id = e.id WHERE e.nombre = '{etiqueta}';"
    ),
    (
        "Reporte de ganancias por categoria",
        "SELECT c.nombre AS categoria, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_totales, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN categoria c ON p.categoria_id = c.id GROUP BY c.nombre ORDER BY ganancia_neta DESC;",
        ["categoria", "unidades_vendidas", "ingresos_totales", "ganancia_neta"]
    ),
    (
        "Reporte de ganancias por marca",
        "SELECT b.nombre AS marca, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_totales, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id GROUP BY b.nombre ORDER BY ganancia_neta DESC;",
        ["marca", "unidades_vendidas", "ingresos_totales", "ganancia_neta"]
    ),
    (
        "Reporte de ganancias por modelo",
        "SELECT m.nombre AS modelo, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_totales, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id GROUP BY m.nombre ORDER BY ganancia_neta DESC;",
        ["modelo", "unidades_vendidas", "ingresos_totales", "ganancia_neta"]
    ),
    (
        "Reporte de ganancias por talla",
        "SELECT t.talla AS talla, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_totales, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN talla t ON pv.id_talla = t.id GROUP BY t.talla ORDER BY ganancia_neta DESC;",
        ["talla", "unidades_vendidas", "ingresos_totales", "ganancia_neta"]
    ),
    (
        "Reporte de ganancias por color",
        "SELECT c.nombre AS color, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_totales, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN color c ON pv.id_color = c.id GROUP BY c.nombre ORDER BY ganancia_neta DESC;",
        ["color", "unidades_vendidas", "ingresos_totales", "ganancia_neta"]
    ),
    (
        "Reporte de ganancias por etiqueta",
        "SELECT e.nombre AS etiqueta, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_totales, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN producto_etiqueta pe ON p.id = pe.producto_id JOIN etiqueta e ON pe.etiqueta_id = e.id GROUP BY e.nombre ORDER BY ganancia_neta DESC;",
        ["etiqueta", "unidades_vendidas", "ingresos_totales", "ganancia_neta"]
    ),
    (
        "Reporte de ganancias por material",
        "SELECT ma.nombre AS material, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_totales, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN material ma ON p.material_id = ma.id GROUP BY ma.nombre ORDER BY ganancia_neta DESC;",
        ["material", "unidades_vendidas", "ingresos_totales", "ganancia_neta"]
    ),
    (
        "Reporte de producto mas rentable",
        "SELECT p.descripcion AS producto, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_neta FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id GROUP BY p.descripcion ORDER BY ganancia_neta DESC LIMIT 10;",
        ["producto", "ganancia_neta"]
    ),
    (
        "Total vendido",
        "SELECT SUM(monto_total) AS ventas_totales FROM venta;"
    ),
    (
        "ventas de ayer",
        "SELECT SUM(monto_total) AS ventas_ayer FROM venta WHERE DATE(fecha_venta) = DATE('now', '-1 day');"
    ),
    (
        "Ventas del vendedor {vendedor_username}",
        "SELECT SUM(v.monto_total) FROM venta v JOIN usuario u ON v.vendedor_id = u.id WHERE u.username = '{vendedor_username}';"
    ),
    (
        "Reporte de ventas por categoria",
        "WITH RECURSIVE categorias_recursivas(id) AS ( SELECT id FROM categoria WHERE nombre = '{categoria}' UNION SELECT c.id FROM categoria c JOIN categorias_recursivas cr ON c.padre_id = cr.id ) SELECT p.descripcion AS producto, m.nombre AS modelo, b.nombre AS marca, SUM(dv.cantidad) AS unidades, SUM(dv.subtotal) AS ingresos FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE p.categoria_id IN (SELECT id FROM categorias_recursivas) GROUP BY p.descripcion, m.nombre, b.nombre ORDER BY ingresos DESC;",
        ["producto", "modelo", "marca", "unidades", "ingresos"]
    ),
    (
        "Reporte de ventas por marca",
        "SELECT b.nombre AS marca, p.descripcion AS producto, SUM(dv.cantidad) AS unidades, SUM(dv.subtotal) AS ingresos FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id GROUP BY b.nombre, p.descripcion ORDER BY b.nombre, ingresos DESC;",
        ["marca", "producto", "unidades", "ingresos"]
    ),
    (
        "Reporte de productos mas vendidos",
        "SELECT p.descripcion AS producto, SUM(dv.cantidad) AS total_vendido, SUM(dv.subtotal) AS ingresos_totales FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id GROUP BY p.descripcion ORDER BY total_vendido DESC LIMIT 10;",
        ["producto", "total_vendido", "ingresos_totales"]
    ),
    (
        "Reporte de inventario del producto {producto}",
        "SELECT t.talla, c.nombre AS color, pv.sku, pv.stock FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id JOIN talla t ON pv.id_talla = t.id JOIN color c ON pv.id_color = c.id WHERE p.descripcion = '{producto}' ORDER BY t.talla, c.nombre;",
        ["talla", "color", "sku", "stock"]
    ),
    (
        "Reporte de productos con bajo stock",
        "SELECT p.descripcion AS producto, pv.sku, pv.stock, t.talla, c.nombre AS color FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id JOIN talla t ON pv.id_talla = t.id JOIN color c ON pv.id_color = c.id WHERE pv.stock < 10 ORDER BY pv.stock ASC;",
        ["producto", "sku", "stock", "talla", "color"]
    ),
    (
        "Lista de productos de la categoria {categoria}",
        "WITH RECURSIVE categorias_recursivas(id) AS ( SELECT id FROM categoria WHERE nombre = '{categoria}' UNION SELECT c.id FROM categoria c JOIN categorias_recursivas cr ON c.padre_id = cr.id ) SELECT p.descripcion AS producto, b.nombre AS marca, m.nombre AS modelo, ma.nombre AS material FROM producto p LEFT JOIN modelo m ON p.modelo_id = m.id LEFT JOIN marca b ON m.marca_id = b.id LEFT JOIN material ma ON p.material_id = ma.id WHERE p.categoria_id IN (SELECT id FROM categorias_recursivas);",
        ["producto", "marca", "modelo", "material"]
    ),
    (
        "Lista de productos de la marca {marca}",
        "SELECT p.descripcion AS producto, m.nombre AS modelo, ma.nombre AS material FROM producto p JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id JOIN material ma ON p.material_id = ma.id WHERE b.nombre = '{marca}';",
        ["producto", "modelo", "material"]
    ),
    (
        "Lista de productos del modelo {modelo}",
        "SELECT p.descripcion AS producto, b.nombre AS marca, ma.nombre AS material, c.nombre AS categoria FROM producto p JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id JOIN material ma ON p.material_id = ma.id JOIN categoria c ON p.categoria_id = c.id WHERE m.nombre = '{modelo}';",
        ["producto", "marca", "material", "categoria"]
    ),
    (
        "Lista de productos del material {material}",
        "SELECT p.descripcion AS producto, b.nombre AS marca, m.nombre AS modelo, c.nombre AS categoria FROM producto p JOIN material ma ON p.material_id = ma.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id JOIN categoria c ON p.categoria_id = c.id WHERE ma.nombre = '{material}';",
        ["producto", "marca", "modelo", "categoria"]
    ),
    (
        "Lista de productos en talla {talla}",
        "SELECT DISTINCT p.descripcion AS producto, b.nombre AS marca, m.nombre AS modelo FROM producto p JOIN prod_variante pv ON p.id = pv.id_producto JOIN talla t ON pv.id_talla = t.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE t.talla = '{talla}';",
        ["producto", "marca", "modelo"]
    ),
    (
        "Lista de productos en color {color}",
        "SELECT DISTINCT p.descripcion AS producto, b.nombre AS marca, m.nombre AS modelo FROM producto p JOIN prod_variante pv ON p.id = pv.id_producto JOIN color c ON pv.id_color = c.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE c.nombre = '{color}';",
        ["producto", "marca", "modelo"]
    ),
    (
        "Lista de productos de la etiqueta {etiqueta}",
        "SELECT p.descripcion AS producto, pv.sku, b.nombre AS marca FROM producto p JOIN producto_etiqueta pe ON p.id = pe.producto_id JOIN etiqueta e ON pe.etiqueta_id = e.id JOIN prod_variante pv ON p.id = pv.id_producto JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE e.nombre = '{etiqueta}';",
        ["producto", "sku", "marca"]
    ),
    (
        "Ventas de los ultimos 30 dias",
        "SELECT SUM(monto_total) AS ventas_30_dias FROM venta WHERE DATE(fecha_venta) >= DATE('now', '-30 days');"
    ),
    (
        "Ventas del año pasado",
        "SELECT SUM(monto_total) AS ventas_ano_pasado FROM venta WHERE STRFTIME('%Y', fecha_venta) = STRFTIME('%Y', DATE('now', '-1 year'));"
    ),
    (
        "Ticket promedio total",
        "SELECT AVG(monto_total) AS ticket_promedio FROM venta;"
    ),
    (
        "Ticket promedio de este mes",
        "SELECT AVG(monto_total) AS ticket_promedio_mes FROM venta WHERE STRFTIME('%Y-%m', fecha_venta) = STRFTIME('%Y-%m', 'now');"
    ),
    (
        "Total de ventas del vendedor {vendedor_username} este mes",
        "SELECT SUM(v.monto_total) FROM venta v JOIN usuario u ON v.vendedor_id = u.id WHERE u.username = '{vendedor_username}' AND STRFTIME('%Y-%m', v.fecha_venta) = STRFTIME('%Y-%m', 'now');"
    ),
    (
        "Numero de ventas de hoy",
        "SELECT COUNT(id) AS num_ventas_hoy FROM venta WHERE DATE(fecha_venta) = DATE('now');"
    ),
    (
        "Cuantas ventas hizo {vendedor_username}",
        "SELECT COUNT(v.id) FROM venta v JOIN usuario u ON v.vendedor_id = u.id WHERE u.username = '{vendedor_username}';"
    ),
    (
        "Reporte de ventas por dia de la semana",
        "SELECT CASE STRFTIME('%w', fecha_venta) WHEN '0' THEN 'Domingo' WHEN '1' THEN 'Lunes' WHEN '2' THEN 'Martes' WHEN '3' THEN 'Miercoles' WHEN '4' THEN 'Jueves' WHEN '5' THEN 'Viernes' ELSE 'Sabado' END AS dia_semana, COUNT(id) AS numero_ventas, SUM(monto_total) AS total_ventas FROM venta GROUP BY dia_semana ORDER BY STRFTIME('%w', fecha_venta);",
        ["dia_semana", "numero_ventas", "total_ventas"]
    ),
    (
        "Reporte de ventas mensuales",
        "SELECT STRFTIME('%Y-%m', fecha_venta) AS mes, COUNT(id) AS numero_ventas, SUM(monto_total) AS total_ventas, AVG(monto_total) AS ticket_promedio FROM venta GROUP BY mes ORDER BY mes DESC;",
        ["mes", "numero_ventas", "total_ventas", "ticket_promedio"]
    ),
    (
        "Reporte de ventas por vendedor",
        "SELECT u.username, u.nombre, u.apellido, COUNT(v.id) AS numero_ventas, SUM(v.monto_total) AS total_vendido, AVG(v.monto_total) AS venta_promedio FROM venta v JOIN usuario u ON v.vendedor_id = u.id GROUP BY u.id, u.username, u.nombre, u.apellido ORDER BY total_vendido DESC;",
        ["username", "nombre", "apellido", "numero_ventas", "total_vendido", "venta_promedio"]
    ),
    (
        "Reporte de clientes por gasto",
        "SELECT u.email, u.nombre, u.apellido, COUNT(v.id) AS total_compras, SUM(v.monto_total) AS gasto_total FROM venta v JOIN usuario u ON v.cliente_id = u.id GROUP BY u.id, u.email, u.nombre, u.apellido ORDER BY gasto_total DESC;",
        ["email", "nombre", "apellido", "total_compras", "gasto_total"]
    ),
    (
        "Reporte por metodo de pago",
        "SELECT metodo_pago, COUNT(id) AS numero_ventas, SUM(monto_total) AS total_recaudado, AVG(monto_total) AS ticket_promedio FROM venta GROUP BY metodo_pago;",
        ["metodo_pago", "numero_ventas", "total_recaudado", "ticket_promedio"]
    ),
    (
        "Reporte por estado de pedido",
        "SELECT estado_pedido, COUNT(id) AS numero_ventas, SUM(monto_total) AS total_recaudado FROM venta GROUP BY estado_pedido;",
        ["estado_pedido", "numero_ventas", "total_recaudado"]
    ),
    (
        "Reporte de las ultimas 20 ventas",
        "SELECT v.fecha_venta, v.numero_venta, u_cliente.email AS cliente, u_vendedor.username AS vendedor, v.monto_total, v.estado_pedido FROM venta v JOIN usuario u_cliente ON v.cliente_id = u_cliente.id JOIN usuario u_vendedor ON v.vendedor_id = u_vendedor.id ORDER BY v.fecha_venta DESC LIMIT 20;",
        ["fecha_venta", "numero_venta", "cliente", "vendedor", "monto_total", "estado_pedido"]
    ),
    (
        "Historial de compras del cliente {cliente_username}",
        "SELECT v.fecha_venta, v.numero_venta, v.monto_total, v.estado_pedido FROM venta v JOIN usuario u ON v.cliente_id = u.id WHERE u.email = '{cliente_username}' ORDER BY v.fecha_venta DESC;",
        ["fecha_venta", "numero_venta", "monto_total", "estado_pedido"]
    ),
    (
        "Cuantos productos base tenemos",
        "SELECT COUNT(id) AS total_productos FROM producto;"
    ),
    (
        "Cuantos SKUs (variantes) tenemos en total",
        "SELECT COUNT(id) AS total_skus FROM prod_variante;"
    ),
    (
        "Valor total del inventario (precio de venta)",
        "SELECT SUM(pv.precio * pv.stock) AS valor_total_venta FROM prod_variante pv;"
    ),
    (
        "Costo total del inventario",
        "SELECT SUM(pv.costo * pv.stock) AS costo_total_inventario FROM prod_variante pv;"
    ),
    (
        "Ganancia potencial total en inventario",
        "SELECT SUM((pv.precio - pv.costo) * pv.stock) AS ganancia_potencial FROM prod_variante pv;"
    ),
    (
        "Stock total de la categoria {categoria}",
        "WITH RECURSIVE categorias_recursivas(id) AS ( SELECT id FROM categoria WHERE nombre = '{categoria}' UNION SELECT c.id FROM categoria c JOIN categorias_recursivas cr ON c.padre_id = cr.id ) SELECT SUM(pv.stock) AS stock_total FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id WHERE p.categoria_id IN (SELECT id FROM categorias_recursivas);"
    ),
    (
        "Stock total del producto {producto}",
        "SELECT SUM(pv.stock) AS stock_total FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id WHERE p.descripcion = '{producto}';"
    ),
    (
        "Cuantos productos en talla {talla} tenemos en stock",
        "SELECT SUM(pv.stock) FROM prod_variante pv JOIN talla t ON pv.id_talla = t.id WHERE t.talla = '{talla}';"
    ),
    (
        "Stock de productos de color {color}",
        "SELECT SUM(pv.stock) FROM prod_variante pv JOIN color c ON pv.id_color = c.id WHERE c.nombre = '{color}';"
    ),
    (
        "Reporte de inventario completo",
        "SELECT p.descripcion AS producto, cat.nombre AS categoria, b.nombre AS marca, m.nombre AS modelo, ma.nombre AS material, pv.sku, t.talla, co.nombre AS color, pv.stock FROM prod_variante pv LEFT JOIN producto p ON pv.id_producto = p.id LEFT JOIN categoria cat ON p.categoria_id = cat.id LEFT JOIN modelo m ON p.modelo_id = m.id LEFT JOIN marca b ON m.marca_id = b.id LEFT JOIN material ma ON p.material_id = ma.id LEFT JOIN talla t ON pv.id_talla = t.id LEFT JOIN color co ON pv.id_color = co.id ORDER BY p.descripcion, pv.stock;",
        ["producto", "categoria", "marca", "modelo", "material", "sku", "talla", "color", "stock"]
    ),
    (
        "Reporte de clientes que compraron {producto}",
        "SELECT u.nombre, u.apellido, u.email, SUM(dv.cantidad) AS unidades_compradas, SUM(dv.subtotal) AS gasto_en_producto FROM detalle_venta dv JOIN venta v ON dv.venta_id = v.id JOIN usuario u ON v.cliente_id = u.id JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id WHERE p.descripcion = '{producto}' GROUP BY u.id, u.nombre, u.apellido, u.email ORDER BY gasto_en_producto DESC;",
        ["nombre", "apellido", "email", "unidades_compradas", "gasto_en_producto"]
    ),
    (
        "Precio promedio de venta del producto {producto}",
        "SELECT AVG(pv.precio) AS precio_promedio FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id WHERE p.descripcion = '{producto}';"
    ),
    (
        "Reporte de ingresos por material",
        "SELECT ma.nombre AS material, SUM(dv.cantidad) AS unidades_vendidas, SUM(dv.subtotal) AS ingresos_por_material FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN material ma ON p.material_id = ma.id GROUP BY ma.nombre ORDER BY ingresos_por_material DESC;",
        ["material", "unidades_vendidas", "ingresos_por_material"]
    ),
    (
        "Reporte de bajo stock (menos de 10 unidades)",
        "SELECT p.descripcion AS producto, pv.sku, t.talla, co.nombre AS color, pv.stock FROM prod_variante pv LEFT JOIN producto p ON pv.id_producto = p.id LEFT JOIN talla t ON pv.id_talla = t.id LEFT JOIN color co ON pv.id_color = co.id WHERE pv.stock < 10 ORDER BY pv.stock ASC;",
        ["producto", "sku", "talla", "color", "stock"]
    ),
    (
        "Reporte de valor de inventario",
        "SELECT p.descripcion AS producto, pv.sku, pv.stock, pv.costo, pv.precio, (pv.stock * pv.costo) AS costo_total, (pv.stock * pv.precio) AS valor_total FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id ORDER BY costo_total DESC;",
        ["producto", "sku", "stock", "costo", "precio", "costo_total", "valor_total"]
    ),
    (
        "Lista de productos de la categoria {categoria}",
        "WITH RECURSIVE categorias_recursivas(id) AS ( SELECT id FROM categoria WHERE nombre = '{categoria}' UNION SELECT c.id FROM categoria c JOIN categorias_recursivas cr ON c.padre_id = cr.id ) SELECT p.descripcion AS producto, b.nombre AS marca, m.nombre AS modelo, ma.nombre AS material FROM producto p LEFT JOIN modelo m ON p.modelo_id = m.id LEFT JOIN marca b ON m.marca_id = b.id LEFT JOIN material ma ON p.material_id = ma.id WHERE p.categoria_id IN (SELECT id FROM categorias_recursivas);",
        ["producto", "marca", "modelo", "material"]
    ),
    (
        "Lista de productos de la marca {marca}",
        "SELECT p.descripcion AS producto, m.nombre AS modelo, ma.nombre AS material, c.nombre AS categoria FROM producto p LEFT JOIN modelo m ON p.modelo_id = m.id LEFT JOIN marca b ON m.marca_id = b.id LEFT JOIN material ma ON p.material_id = ma.id LEFT JOIN categoria c ON p.categoria_id = c.id WHERE b.nombre = '{marca}';",
        ["producto", "modelo", "material", "categoria"]
    ),
    (
        "Lista de productos con la etiqueta {etiqueta}",
        "SELECT p.descripcion AS producto, b.nombre AS marca, m.nombre AS modelo, c.nombre AS categoria FROM producto p JOIN producto_etiqueta pe ON p.id = pe.producto_id JOIN etiqueta e ON pe.etiqueta_id = e.id LEFT JOIN modelo m ON p.modelo_id = m.id LEFT JOIN marca b ON m.marca_id = b.id LEFT JOIN categoria c ON p.categoria_id = c.id WHERE e.nombre = '{etiqueta}';",
        ["producto", "marca", "modelo", "categoria"]
    ),
    (
        "Lista de productos de {material}",
        "SELECT p.descripcion AS producto, b.nombre AS marca, m.nombre AS modelo FROM producto p JOIN material ma ON p.material_id = ma.id LEFT JOIN modelo m ON p.modelo_id = m.id LEFT JOIN marca b ON m.marca_id = b.id WHERE ma.nombre = '{material}';",
        ["producto", "marca", "modelo"]
    ),
    (
        "Reporte de inventario del producto {producto}",
        "SELECT t.talla, c.nombre AS color, pv.sku, pv.stock, pv.costo, pv.precio FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id LEFT JOIN talla t ON pv.id_talla = t.id LEFT JOIN color c ON pv.id_color = c.id WHERE p.descripcion = '{producto}' ORDER BY t.talla, c.nombre;",
        ["talla", "color", "sku", "stock", "costo", "precio"]
    ),
    (
        "Total de clientes registrados",
        "SELECT COUNT(u.id) FROM usuario u JOIN rol r ON u.rol_id = r.id WHERE r.nombre = 'CLIENTE';"
    ),
    (
        "Total de compras del cliente {cliente_username}",
        "SELECT SUM(v.monto_total) FROM venta v JOIN usuario u ON v.cliente_id = u.id WHERE u.email = '{cliente_username}';"
    ),
    (
        "Cuantas compras hizo {cliente_username}",
        "SELECT COUNT(v.id) FROM venta v JOIN usuario u ON v.cliente_id = u.id WHERE u.email = '{cliente_username}';"
    ),
    (
        "Gasto promedio por cliente",
        "SELECT AVG(total_gasto) FROM (SELECT SUM(monto_total) AS total_gasto FROM venta GROUP BY cliente_id) AS gastos_cliente;"
    ),
    (
        "Reporte de clientes por gasto",
        "SELECT u.nombre, u.apellido, u.email, u.telefono, COUNT(v.id) AS total_compras, SUM(v.monto_total) AS gasto_total FROM venta v JOIN usuario u ON v.cliente_id = u.id JOIN rol r ON u.rol_id = r.id WHERE r.nombre = 'CLIENTE' GROUP BY u.id, u.nombre, u.apellido, u.email, u.telefono ORDER BY gasto_total DESC;",
        ["nombre", "apellido", "email", "telefono", "total_compras", "gasto_total"]
    ),
    (
        "Reporte de clientes por numero de compras",
        "SELECT u.nombre, u.apellido, u.email, u.telefono, COUNT(v.id) AS total_compras, SUM(v.monto_total) AS gasto_total FROM venta v JOIN usuario u ON v.cliente_id = u.id JOIN rol r ON u.rol_id = r.id WHERE r.nombre = 'CLIENTE' GROUP BY u.id, u.nombre, u.apellido, u.email, u.telefono ORDER BY total_compras DESC;",
        ["nombre", "apellido", "email", "telefono", "total_compras", "gasto_total"]
    ),
    (
        "Lista de clientes y sus direcciones",
        "SELECT u.nombre, u.apellido, u.email, d.departamento, d.zona, d.calle FROM usuario u LEFT JOIN direccion d ON u.id = d.usuario_id JOIN rol r ON u.rol_id = r.id WHERE r.nombre = 'CLIENTE' ORDER BY u.apellido;",
        ["nombre", "apellido", "email", "departamento", "zona", "calle"]
    ),
    (
        "Reporte de productos comprados por {cliente_username}",
        "SELECT p.descripcion AS producto, pv.sku, SUM(dv.cantidad) AS unidades_compradas FROM detalle_venta dv JOIN venta v ON dv.venta_id = v.id JOIN usuario u ON v.cliente_id = u.id JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id WHERE u.email = '{cliente_username}' GROUP BY p.descripcion, pv.sku ORDER BY unidades_compradas DESC;",
        ["producto", "sku", "unidades_compradas"]
    ),
    (
        "Historial de compras del cliente {cliente_username}",
        "SELECT v.fecha_venta, v.numero_venta, v.monto_total, v.estado_pedido FROM venta v JOIN usuario u ON v.cliente_id = u.id WHERE u.email = '{cliente_username}' ORDER BY v.fecha_venta DESC;",
        ["fecha_venta", "numero_venta", "monto_total", "estado_pedido"]
    )
]

# --- 2. Funcion para cargar los datos de tus CSVs (¡CAMBIO!) ---
def cargar_parametros():
    """Carga los datos de los CSVs en listas para usarlos en las plantillas."""
    try:
        df_productos = pd.read_csv("./data_csvs/productos_data.csv", sep=';', header=None)
        df_categorias = pd.read_csv("./data_csvs/categorias_data.csv", sep=',', header=None)
        df_usuarios = pd.read_csv("./data_csvs/usuarios_data.csv", sep=',', header=None)
        df_variantes = pd.read_csv("./data_csvs/prod_variantes_data.csv", sep=';', header=None)
        df_etiquetas = pd.read_csv("./data_csvs/etiquetas_data.csv", sep=',', header=None)
        df_marcas = pd.read_csv("./data_csvs/marcas_data.csv", sep=',', header=None)
        df_modelos = pd.read_csv("./data_csvs/modelos_data.csv", sep=',', header=None)
        df_materiales = pd.read_csv("./data_csvs/materiales_data.csv", sep=',', header=None)
        df_tallas = pd.read_csv("./data_csvs/tallas_data.csv", sep=',', header=None)
        df_colores = pd.read_csv("./data_csvs/colores_data.csv", sep=',', header=None)

        parametros = {
            "producto": df_productos[0].dropna().tolist(),
            "categoria": df_categorias[0].dropna().tolist(),
            "vendedor_username": df_usuarios[df_usuarios[6] == 'VENDEDOR'][0].dropna().tolist(),
            "sku": df_variantes[6].dropna().tolist(),
            "etiqueta": df_etiquetas[0].dropna().tolist(),
            "marca": df_marcas[0].dropna().tolist(),
            "modelo": df_modelos[0].dropna().tolist(),
            "material": df_materiales[0].dropna().tolist(),
            "talla": df_tallas[0].dropna().tolist(),
            "color": df_colores[0].dropna().tolist(),
            "metodo_pago": ["Tarjeta", "Efectivo", "QR"],
            "estado_pedido": ["pendiente", "enviado", "entregado", "cancelado"],
            # --- ¡CAMBIO! Añadido el que faltaba ---
            "cliente_username": df_usuarios[df_usuarios[6] == 'CLIENTE'][0].dropna().tolist()


        }
        
        for key, val in parametros.items():
            if not val:
                print(f"Advertencia: No se encontraron datos para '{key}'.")
        
        return parametros
        
    except FileNotFoundError as e:
        print(f"Error: No se encontro el archivo {e.filename}.")
        print("Asegurate de haber creado la carpeta 'data_csvs' y copiado todos los .csv alli.")
        return None
    except Exception as e:
        print(f"Error cargando CSVs: {e}")
        return None

# --- 3. Script de Generacion (¡CAMBIO COMPLETO!) ---

def generar_dataset(params, num_samples=2000, nombre_archivo="train.jsonl"):
    """
    Genera un dataset de num_samples ejemplos.
    - El prompt incluye formato.
    - El prompt A VECES incluye seleccion de columnas.
    - La salida es un string JSON {"sql", "formato", "columnas"}.
    """
    
    print(f"Generando {num_samples} muestras avanzadas en {nombre_archivo}...")
    
    formatos = ["pdf", "excel", "json"]
    prompt_formatos = {
        "pdf": ["en pdf", "para un pdf", "genera un pdf de"],
        "excel": ["en excel", "para excel", "en un archivo excel", "genera un excel de"],
        "json": ["en json", "devuelve un json con", ""] 
    }

    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        count = 0
        while count < num_samples:
            
            # --- 1. Elegir Plantilla y Formato ---
            plantilla = random.choice(TEMPLATES)
            formato_elegido = random.choice(formatos)
            variacion_prompt_fmt = random.choice(prompt_formatos[formato_elegido])

            texto_base = plantilla[0]
            sql_final = plantilla[1]
            
            # Columnas por defecto (lista vacia)
            columnas_elegidas = []
            
            # --- 2. Logica de Seleccion de Columnas (¡NUEVO!) ---
            # Si la plantilla tiene 3 elementos (es una plantilla de tabla)
            # y decidimos aleatoriamente (50% de las veces) pedir columnas especificas
            if len(plantilla) == 3 and random.choice([True, False]):
                columnas_disponibles = plantilla[2]
                
                # Elegir 2 o 3 columnas al azar de la lista
                num_cols = random.randint(2, 3)
                columnas_elegidas = random.sample(columnas_disponibles, k=min(num_cols, len(columnas_disponibles)))
                
                # Crear el texto para el prompt
                texto_cols = ", ".join(columnas_elegidas)
                variaciones_col_prompt = [
                    f"mostrando solo {texto_cols}",
                    f"columnas: {texto_cols}",
                    f"dame solo {texto_cols}"
                ]
                texto_base = f"{texto_base} {random.choice(variaciones_col_prompt)}"

            # --- 3. Construir Prompt de Entrada ---
            if variacion_prompt_fmt.startswith("genera un"):
                texto_final = f"genera un {formato_elegido} de {texto_base}"
            elif variacion_prompt_fmt:
                texto_final = f"{texto_base} {variacion_prompt_fmt}"
            else:
                texto_final = texto_base
            
            texto_final = "generar JSON: " + texto_final.lower()

            # --- 4. Llenar Placeholders (¡CAMBIO!) ---
            skip_plantilla = False
            # --- ¡CAMBIO! Añadido 'cliente_email' ---
            placeholders = {
                "{producto}": "producto", "{categoria}": "categoria",
                "{vendedor_username}": "vendedor_username", "{sku}": "sku",
                "{etiqueta}": "etiqueta", "{marca}": "marca",
                "{modelo}": "modelo", "{material}": "material",
                "{talla}": "talla", "{color}": "color",
                "{metodo_pago}": "metodo_pago", "{estado_pedido}": "estado_pedido",
                "{cliente_username}": "cliente_username" # <-- Añadido
            }
            
            for ph, key in placeholders.items():
                if ph in texto_final:
                    # Usamos .get() para manejar claves que podrian no estar (aunque ahora deberian estar todas)
                    if not params.get(key): 
                        skip_plantilla = True
                        break
                    valor = random.choice(params[key])
                    texto_final = texto_final.replace(ph, str(valor))
                    sql_final = sql_final.replace(ph, str(valor).replace("'", "''"))
            
            if skip_plantilla:
                continue

            # --- 5. Construir JSON de Salida (¡NUEVO!) ---
            salida_dict = {
                "sql": sql_final,
                "formato": formato_elegido,
                "columnas": columnas_elegidas  # Se añade la lista (vacia o llena)
            }
            salida_json_string = json.dumps(salida_dict) 

            # --- 6. Escribir en el archivo ---
            linea_dataset = {"texto": texto_final, "salida_json": salida_json_string}
            f.write(json.dumps(linea_dataset, ensure_ascii=False) + '\n')
            count += 1
            
    print(f"¡Dataset avanzado '{nombre_archivo}' generado con {num_samples} lineas!")


if __name__ == "__main__":
    parametros = cargar_parametros()
    if parametros:
        # ¡Aumentemos el numero de muestras!
        generar_dataset(parametros, num_samples=8000, nombre_archivo="train.jsonl")