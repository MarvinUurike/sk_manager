import json
import uuid
from datetime import datetime
import os
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Key
from aws_utils import get_table
from equipment import get_equipment
from db import log_lending_history

# dynamodb is initialized lazily
# dynamodb = None # This is no longer needed as get_table is externalized

# def get_dynamodb(): # This is no longer needed as get_table is externalized
#     global dynamodb
#     if dynamodb is None:
#         import boto3
#         dynamodb = boto3.resource('dynamodb')
#     return dynamodb

# def get_table(env_var_name): # This is no longer needed as get_table is externalized
#     import os
#     return get_dynamodb().Table(os.environ.get(env_var_name))

def list_lendings() -> List[Dict[str, Any]]:
    table = get_table('LENDING_TABLE')
    # Filter for active lendings (where returned_date is null or empty)
    response = table.scan()
    items = response.get('Items', [])
    active_lendings = [item for item in items if not item.get('returned_date')]
    return active_lendings

def lend_item(equipment_id, data):
    if 'borrower' not in data or 'quantity' not in data:
        raise ValueError("Missing required fields: borrower, quantity")
        
    quantity_to_lend = int(data['quantity'])
    if quantity_to_lend <= 0:
        raise ValueError("Lend quantity must be > 0")
        
    # Check if we have enough in stock
    equipment = get_equipment(equipment_id)
    if not equipment:
        raise ValueError("Equipment not found")
        
    total_quantity = int(equipment.get('quantity', 0))
    
    # Calculate currently lent out quantity
    table = get_table('LENDING_TABLE')
    response = table.query(
        IndexName='EquipmentIndex',
        KeyConditionExpression=Key('equipment_id').eq(equipment_id)
    )
    
    currently_lent = 0
    for item in response.get('Items', []):
        if not item.get('returned_date'):
            currently_lent += int(item.get('quantity', 0))
            
    available = total_quantity - currently_lent
    
    if quantity_to_lend > available:
        raise ValueError(f"Not enough items available. Total: {total_quantity}, Lent: {currently_lent}, Available: {available}")
        
    lending_id = str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    item = {
        'lending_id': lending_id,
        'equipment_id': equipment_id,
        'borrower': data['borrower'],
        'quantity': quantity_to_lend,
        'lent_date': now_iso,
        'returned_date': None
    }
    
    table.put_item(Item=item)
    
    # Log to PostgreSQL History
    try:
        log_lending_history(lending_id, equipment_id, data['borrower'], quantity_to_lend, 'LEND')
    except Exception as e:
        print(f"Failed to log history: {e}")
        
    return item

def return_item(equipment_id, data):
    if 'lending_id' not in data:
        raise ValueError("Missing required field: lending_id")
        
    lending_id = data['lending_id']
    table = get_table('LENDING_TABLE')
    
    # Get the lending record to verify it exists and belongs to this equipment
    response = table.get_item(Key={'lending_id': lending_id})
    lending = response.get('Item')
    
    if not lending:
        raise ValueError("Lending record not found")
        
    if lending.get('equipment_id') != equipment_id:
        raise ValueError("Lending record does not match equipment ID")
        
    if lending.get('returned_date'):
        raise ValueError("Item already returned")
        
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    updated = table.update_item(
        Key={'lending_id': lending_id},
        UpdateExpression="SET returned_date = :date_val",
        ExpressionAttributeValues={":date_val": now_iso},
        ReturnValues="ALL_NEW"
    )
    
    result = updated.get('Attributes', {})
    
    # Log to PostgreSQL History
    try:
        log_lending_history(lending_id, equipment_id, lending.get('borrower'), lending.get('quantity'), 'RETURN')
    except Exception as e:
        print(f"Failed to log history: {e}")
        
    return result
