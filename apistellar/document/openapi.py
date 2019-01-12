import json

from apistar.codecs import JSONSchemaCodec
from apistar.codecs.openapi import OpenAPICodec as _OpenAPICodec, OPEN_API

from ..helper import TypeEncoder

from apistar.server import handlers


class OpenAPICodec(_OpenAPICodec):
    media_type = 'application/vnd.oai.openapi'
    format = 'openapi'

    def encode(self, document, **options):
        schema_defs = {}
        paths = self.get_paths(document, schema_defs=schema_defs)
        openapi = OPEN_API.validate({
            'openapi': '3.0.0',
            'info': {
                'version': document.version,
                'title': document.title,
                'description': document.description
            },
            'servers': [{
                'url': document.url
            }],
            'paths': paths
        })

        if schema_defs:
            openapi['components'] = {'schemas': schema_defs}

        if not document.url:
            openapi.pop('servers')

        kwargs = {
            'ensure_ascii': False,
            'indent': 4,
            'separators': (',', ': ')
        }
        return json.dumps(openapi, cls=TypeEncoder, **kwargs).encode('utf-8')

    def get_operation(self, link, operation_id, tag=None, schema_defs=None):
        operation = {
            'operationId': operation_id
        }
        if link.title:
            operation['summary'] = link.title
        if link.description:
            operation['description'] = link.description
        if tag:
            operation['tags'] = [tag]
        if link.get_path_fields() or link.get_query_fields():
            operation['parameters'] = [
                self.get_parameter(field, schema_defs) for field in
                link.get_path_fields() + link.get_query_fields()
            ]
        if link.get_body_field():
            schema = link.get_body_field().schema
            if schema is None:
                content_info = {}
            else:
                content_info = {
                    'schema': JSONSchemaCodec().encode_to_data_structure(
                        schema,
                        schema_defs,
                        '#/components/schemas/'
                    )
                }

            operation['requestBody'] = {
                'content': {
                    link.encoding: content_info
                }
            }

        if link.response is not None:
            operation['responses'] = {
                str(link.response.status_code): {
                    'description': link.response.description,
                    'content': {
                        link.response.encoding: {
                            'schema': JSONSchemaCodec().encode_to_data_structure(
                                link.response.schema,
                                schema_defs,
                                '#/components/schemas/'
                            )
                        }
                    }
                }
            }
        return operation


handlers.OpenAPICodec = OpenAPICodec
