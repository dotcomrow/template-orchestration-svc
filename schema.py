from marshmallow import Schema, fields

class BaseSchema(Schema):
    code = fields.Str(required=True)
    value = fields.Str(required=True)
    
    def to_dict():
        return {
            'code': 'string',
            'value': 'string'
        }
