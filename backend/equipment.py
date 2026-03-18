import json
import json
import uuid
import os
from typing import List, Dict, Any, Optional
from aws_utils import get_table
from db import log_equipment_history

def list_equipment() -> List[Dict[str, Any]]:
    table = get_table('EQUIPMENT_TABLE')
    response = table.scan()
    return response.get('Items', [])

def get_equipment(equipment_id: str) -> Optional[Dict[str, Any]]:
    table = get_table('EQUIPMENT_TABLE')
    response = table.get_item(Key={'id': equipment_id})
    return response.get('Item')

def create_equipment(data):
    table = get_table('EQUIPMENT_TABLE')
    
    if 'name' not in data or 'quantity' not in data:
        raise ValueError("Missing required fields: name, quantity")
        
    equipment_id = str(uuid.uuid4())
    
    item = {
        'equipment_id': equipment_id,
        'name': data['name'],
        'quantity': int(data['quantity']),
        'location': data.get('location', ''),
        'photo_url': ''
    }
    
    table.put_item(Item=item)
    
    # Log to PostgreSQL History
    try:
        log_equipment_history(equipment_id, 'CREATE', item)
    except Exception as e:
        print(f"Failed to log history: {e}")
        
    return item

def update_equipment(equipment_id, data):
    table = get_table('EQUIPMENT_TABLE')
    
    # Fetch existing to get current values not being updated
    existing = get_equipment(equipment_id)
    if not existing:
        raise ValueError("Equipment not found")
        
    # Build update expression dynamically based on provided data
    update_exp = "SET "
    exp_attr_names = {}
    exp_attr_vals = {}
    
    updatable_fields = ['name', 'quantity', 'location', 'photo_url']
    
    count = 0
    for field in updatable_fields:
        if field in data:
            if count > 0: update_exp += ", "
            update_exp += f"#{field} = :{field}"
            exp_attr_names[f"#{field}"] = field
            exp_attr_vals[f":{field}"] = data[field]
            count += 1
            
    if count == 0:
        return existing
        
    updated = table.update_item(
        Key={'equipment_id': equipment_id},
        UpdateExpression=update_exp,
        ExpressionAttributeNames=exp_attr_names,
        ExpressionAttributeValues=exp_attr_vals,
        ReturnValues="ALL_NEW"
    )
    
    result = updated.get('Attributes', {})
    
    # Log to PostgreSQL History
    try:
        log_equipment_history(equipment_id, 'UPDATE', result)
    except Exception as e:
        print(f"Failed to log history: {e}")
        
    return result

def delete_equipment(equipment_id):
    table = get_table('EQUIPMENT_TABLE')
    table.delete_item(Key={'equipment_id': equipment_id})
    
    # Log to PostgreSQL History
    try:
        log_equipment_history(equipment_id, 'DELETE')
    except Exception as e:
        print(f"Failed to log history: {e}")
        
    return {"status": "deleted"}
