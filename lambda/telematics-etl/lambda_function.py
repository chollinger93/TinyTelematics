import json
import base64
import uuid


def lambda_handler(event, context):
    # print(event)
    output_data = []
    for record in event['records']:
        success = []
        failed = []
        payload = base64.b64decode(record['data'])
        data = json.loads(payload)
        for elem in data:
            # print(elem)
            _elem = json.loads(elem)
            # TODO: temp disallow lat/long 0
            # Lat/long are required, unless we want to wind up in the Atlantic ocean
            if False:  # _elem['lat'] == 0 or _elem['long'] == 0:
                print('Lat/Long is invalid')
                failed.append(_elem)
            else:
                # Filter default values and assign reasonable defaults
                if _elem['speed'] == 'nan':
                    _elem['speed'] = -999
                if _elem['altitude'] == 'nan':
                    _elem['altitude'] = -999
                success.append(_elem)
        # Output ready for Athena, one JSON element per line, no arrays
        _outputstr = ''
        for js in success:
            _outputstr += str(json.dumps(js).encode('utf-8')) + '\n'
        # TODO: ugly hack with base64 encoding late at night
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(json.dumps(_outputstr).replace('\\n', '\n').replace('\\', '').replace('b\'','').encode("utf-8")).decode('utf-8')
        }
        output_data.append(output_record)
    print('Successfully processed {} records.'.format(len(event['records'])))

    print(output_data)
    return {'records': output_data}
