import json
import decimal
import traceback
from typing import Dict, Any

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)

def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Helper to build consistent API Gateway proxy responses"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def handler(event, context):
    # Log incident for debugging
    # print(f"EVENT: {json.dumps(event)}")
    
    path = event.get('path', '/')
    # Handle /v1 prefix if present
    if path.startswith('/v1'):
        path = path[3:] or '/'
    
    method = event.get('httpMethod')
    query_params = event.get('queryStringParameters') or {}
    
    try:
        body = json.loads(event.get('body') or '{}')
    except Exception:
        body = {}

    try:
        # PING
        if path == '/ping':
            return build_response(200, {"status": "ok", "environment": "modular"})

        # DEBUG DB
        if path == '/debug/db':
            import db
            db.init_db_schema() # Ensure tables exist
            conn = db.get_db_connection()
            if conn:
                return build_response(200, {"status": "Database connected and schema initialized"})
            return build_response(500, {"error": "Database connection failed"})

        # EQUIPMENT
        if path == '/equipment':
            import equipment
            if method == 'GET':
                return build_response(200, equipment.list_equipment())
            if method == 'POST':
                return build_response(201, equipment.create_equipment(body))

        if path.startswith('/equipment/'):
            import equipment
            eq_id = path.split('/')[-1]
            if method == 'GET':
                item = equipment.get_equipment(eq_id)
                return build_response(200, item) if item else build_response(404, {"error": "Not found"})
            if method == 'PUT':
                return build_response(200, equipment.update_equipment(eq_id, body))
            if method == 'DELETE':
                return build_response(200, equipment.delete_equipment(eq_id))

        # LENDINGS
        if path == '/lendings':
            import lending
            if method == 'GET':
                return build_response(200, lending.list_lendings())
            if method == 'POST':
                return build_response(201, lending.lend_item(body))

        if path == '/lendings/return':
            import lending
            if method == 'POST':
                return build_response(200, lending.return_item(body))

        # PHOTOS
        if path == '/photos/upload-url':
            import photos
            eq_id = query_params.get('id')
            content_type = query_params.get('content_type', 'image/jpeg')
            return build_response(200, photos.get_upload_url(eq_id, content_type))

        # HISTORY
        if path == '/history':
            import db
            eq_id = query_params.get('id')
            return build_response(200, db.get_equipment_history(eq_id))

        return build_response(404, {"error": f"Path {path} not found"})

    except Exception as e:
        print(f"CRITICAL ERROR: {traceback.format_exc()}")
        return build_response(500, {"error": str(e)})
