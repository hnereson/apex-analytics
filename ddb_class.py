import boto3
from decimal import Decimal 
import math
import uuid
import streamlit as st
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key

MASTER_ACCESS_KEY = st.secrets['MASTER_ACCESS_KEY']
MASTER_SECRET = st.secrets['MASTER_SECRET']

class DDB: 

    def __init__(self, table: str):  

        self.table = table

        # resource  
        self.resource = boto3.resource('dynamodb', 
                          aws_access_key_id=MASTER_ACCESS_KEY, 
                          aws_secret_access_key=MASTER_SECRET, 
                          region_name='us-west-1')
        
        # table 
        self.table = self.resource.Table(self.table)

        # client 
        self.client = boto3.client('dynamodb', 
                               aws_access_key_id=MASTER_ACCESS_KEY, 
                               aws_secret_access_key=MASTER_SECRET, 
                               region_name='us-west-1')   
    st.cache(ttl=60*60*24)
    def query_items(self, include_conditions=None, exclude_conditions=None):
        filter_expression = None

        if include_conditions:
            for attribute, value in include_conditions.items():
                condition = Attr(attribute).eq(value)
                if filter_expression is None:
                    filter_expression = condition
                else:
                    filter_expression &= condition

        if exclude_conditions:
            for attribute, value in exclude_conditions.items():
                condition = ~Attr(attribute).eq(value)
                if filter_expression is None:
                    filter_expression = condition
                else:
                    filter_expression &= condition

        if filter_expression is not None:
            response = self.table.scan(FilterExpression=filter_expression)
        else:
            response = self.table.scan()

        items = response['Items']
        return items

    def get_id(self): return str(uuid.uuid4()) 

    st.cache(ttl=60*60*24)
    def list_items(self):
        response = self.table.scan()
        items = response['Items']

        while 'LastEvaluatedKey' in response:
            response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        return items 
    
    def convert_floats_to_decimals(self, obj):
        if isinstance(obj, float):
            if obj == float('inf') or obj == float('-inf') or math.isnan(obj):
                # Handle Infinity and NaN here. For example, replacing with 0:
                return ''
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = self.convert_floats_to_decimals(v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                obj[i] = self.convert_floats_to_decimals(v)
        return obj

    def fetch_by_id(self, _id: str): 
        return self.table.get_item(Key={'id': _id})
    
    def fetch_by_key(self, key_value):
        return self.table.get_item(Key={'id': key_value})
    
    def delete_item(self, _id: str): 

        assert type(_id) == str, "id must be a string"

        key = {
            "id": _id
        }

        return self.table.delete_item(Key=key)
    
    def put_item(self, item: dict):
        item = self.convert_floats_to_decimals(item) 
        if 'id' not in item.keys(): 
            item['id'] = self.get_id() 
            
        return self.table.put_item(Item=item)
    
    def query_by_index(self, query_params):
        """
        Queries the table using a specified index.

        :param query_params: Dictionary with 'index', 'field', and 'value' as keys.
        :return: List of items matching the query parameters.
        """
        if not all(k in query_params for k in ('index', 'field', 'value')):
            raise ValueError("Query parameters must include 'index', 'field', and 'value'.")

        index_name = query_params['index']
        query_field = query_params['field']
        query_value = query_params['value']
        
        response = self.table.query(
            IndexName=index_name,
            KeyConditionExpression=Key(query_field).eq(query_value)
        )
        
        return response['Items']
    
