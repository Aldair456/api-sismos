import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    # URL de la página web que contiene la tabla de sismos
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    # Realizar la solicitud HTTP a la página web
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web'
        }

    # Parsear el contenido HTML de la página web
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontrar la tabla en el HTML que contiene los sismos
    table = soup.find('table')
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla en la página web'
        }

    # Extraer los encabezados de la tabla
    headers = [header.text.strip() for header in table.find_all('th')]

    # Extraer las filas de la tabla y los 10 últimos sismos
    rows = []
    for row in table.find_all('tr')[1:11]:  # Solo obtener las primeras 10 filas
        cells = row.find_all('td')
        rows.append({
            "Fecha": cells[0].text.strip(),
            "Latitud": cells[1].text.strip(),
            "Longitud": cells[2].text.strip(),
            "Profundidad": cells[3].text.strip(),
            "Magnitud": cells[4].text.strip(),
            "Ubicación": cells[5].text.strip(),
            "id": str(uuid.uuid4())  # Generar un ID único para cada entrada
        })

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('EarthquakesTable')

    # Eliminar todos los elementos de la tabla antes de agregar los nuevos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    # Insertar los nuevos datos
    with table.batch_writer() as batch:
        for row in rows:
            batch.put_item(Item=row)

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': rows
    }
