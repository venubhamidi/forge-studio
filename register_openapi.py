#!/usr/bin/env python3
"""
OpenAPI to MCP Gateway Registration Script

This script parses an OpenAPI 3.0 specification and automatically registers
each endpoint as an MCP tool in the mcp-context-forge gateway.
"""

import json
import os
import sys
import requests
import yaml
from typing import Dict, List, Any
from pathlib import Path


class OpenAPIToMCP:
    def __init__(self, gateway_url: str, bearer_token: str):
        self.gateway_url = gateway_url.rstrip('/')
        self.bearer_token = bearer_token
        self.headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }
    
    def parse_openapi_spec(self, spec_path: str) -> Dict[str, Any]:
        """Load and parse OpenAPI spec from YAML or JSON file"""
        with open(spec_path, 'r') as f:
            if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def convert_openapi_to_json_schema(self, openapi_schema: Dict) -> Dict:
        """Convert OpenAPI schema to JSON Schema format"""
        # Basic conversion - handles common cases
        json_schema = {
            "type": "object",
            "properties": {}
        }
        
        if 'properties' in openapi_schema:
            json_schema['properties'] = openapi_schema['properties']
        
        if 'required' in openapi_schema:
            json_schema['required'] = openapi_schema['required']
        
        return json_schema
    
    def extract_parameters(self, operation: Dict, path: str) -> Dict:
        """Extract parameters from OpenAPI operation and convert to JSON schema"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Handle path parameters
        if 'parameters' in operation:
            for param in operation['parameters']:
                if param['in'] == 'path':
                    param_name = param['name']
                    schema['properties'][param_name] = {
                        "type": param.get('schema', {}).get('type', 'string'),
                        "description": param.get('description', f'Path parameter: {param_name}')
                    }
                    if param.get('required', False):
                        schema['required'].append(param_name)
        
        # Handle request body
        if 'requestBody' in operation:
            req_body = operation['requestBody']
            if 'content' in req_body:
                for content_type, content in req_body['content'].items():
                    if 'application/json' in content_type and 'schema' in content:
                        body_schema = content['schema']
                        
                        # If it's a reference, we need to resolve it (simplified)
                        if '$ref' in body_schema:
                            # For now, just note that body is required
                            schema['properties']['body'] = {
                                "type": "object",
                                "description": "Request body (see OpenAPI spec for full schema)"
                            }
                        else:
                            # Merge body schema properties into main schema
                            if 'properties' in body_schema:
                                schema['properties'].update(body_schema['properties'])
                            if 'required' in body_schema:
                                schema['required'].extend(body_schema['required'])
        
        return schema
    
    def register_tool(self, tool_data: Dict) -> Dict:
        """Register a single tool with the MCP gateway"""
        wrapped_data = {"tool": tool_data}
        response = requests.post(
            f'{self.gateway_url}/tools',
            headers=self.headers,
            json=wrapped_data
        )
        response.raise_for_status()
        return response.json()
    
    def create_virtual_server(self, name: str, description: str, tool_ids: List[str]) -> Dict:
        """Create a virtual MCP server with the registered tools"""
        server_data = {
            "server": {
                "name": name,
                "description": description,
                "associatedTools": tool_ids
            }
        }

        response = requests.post(
            f'{self.gateway_url}/servers',
            headers=self.headers,
            json=server_data
        )

        if not response.ok:
            print(f"❌ Server creation failed with status {response.status_code}")
            print(f"Response: {response.text}")

        response.raise_for_status()
        return response.json()
    
    def register_openapi_spec(self, spec_path: str, api_name: str = None) -> Dict:
        """Register all endpoints from an OpenAPI spec"""
        print(f"📖 Loading OpenAPI spec from: {spec_path}")
        spec = self.parse_openapi_spec(spec_path)
        
        if api_name is None:
            api_name = spec.get('info', {}).get('title', 'api-server')
        
        api_description = spec.get('info', {}).get('description', '')
        base_url = spec.get('servers', [{}])[0].get('url', 'http://localhost:8000')
        
        print(f"📦 API: {api_name}")
        print(f"🌐 Base URL: {base_url}")
        print(f"📄 Description: {api_description[:100]}...")
        print()
        
        tool_ids = []
        paths = spec.get('paths', {})
        
        print(f"🔧 Registering {len(paths)} endpoints as MCP tools...")
        print()
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    continue
                
                operation_id = operation.get('operationId', f"{method}_{path.replace('/', '_')}")
                summary = operation.get('summary', '')
                description = operation.get('description', summary)
                
                # Build full URL with path
                full_url = f"{base_url.rstrip('/')}{path}"
                
                # Extract and convert parameters
                input_schema = self.extract_parameters(operation, path)
                
                tool_data = {
                    "name": operation_id,
                    "url": full_url,
                    "description": description or summary,
                    "integration_type": "REST",
                    "request_type": method.upper(),
                    "input_schema": input_schema
                }
                
                print(f"  🔹 Registering: {operation_id} ({method.upper()} {path})")
                
                try:
                    result = self.register_tool(tool_data)
                    tool_id = result.get('id') or result.get('tool_id')
                    tool_ids.append(tool_id)
                    print(f"     ✓ Created with ID: {tool_id}")
                except Exception as e:
                    print(f"     ✗ Failed: {e}")
        
        print()
        print(f"✅ Registered {len(tool_ids)} tools")
        print()
        
        # Create virtual server
        print("🖥️  Creating virtual MCP server...")
        server_name = api_name.lower().replace(' ', '-')
        server = self.create_virtual_server(server_name, api_description, tool_ids)
        
        server_uuid = server.get('id') or server.get('uuid')
        print(f"✅ Virtual server created: {server_uuid}")
        
        return {
            "server_uuid": server_uuid,
            "tool_ids": tool_ids,
            "tool_count": len(tool_ids),
            "api_name": api_name,
            "base_url": base_url
        }


def main():
    # Configuration
    GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:4444')
    BEARER_TOKEN = os.getenv('MCPGATEWAY_BEARER_TOKEN')
    
    if not BEARER_TOKEN:
        print("❌ Error: MCPGATEWAY_BEARER_TOKEN environment variable not set")
        print("   Run: export MCPGATEWAY_BEARER_TOKEN=<your-token>")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python register_openapi.py <openapi-spec.yaml>")
        print()
        print("Environment variables:")
        print("  GATEWAY_URL - MCP Gateway URL (default: http://localhost:4444)")
        print("  MCPGATEWAY_BEARER_TOKEN - JWT bearer token for authentication")
        sys.exit(1)
    
    spec_path = sys.argv[1]
    
    if not Path(spec_path).exists():
        print(f"❌ Error: File not found: {spec_path}")
        sys.exit(1)
    
    print("🚀 OpenAPI to MCP Gateway Registration")
    print("=" * 50)
    print()
    
    converter = OpenAPIToMCP(GATEWAY_URL, BEARER_TOKEN)
    
    try:
        result = converter.register_openapi_spec(spec_path)
        
        print()
        print("=" * 50)
        print("🎉 Registration Complete!")
        print("=" * 50)
        print()
        print(f"📡 Streamable HTTP Endpoint:")
        print(f"   {GATEWAY_URL}/servers/{result['server_uuid']}/mcp")
        print()
        print(f"📊 Registered Tools: {result['tool_count']}")
        print()
        
        # Save configuration
        config = {
            "server_uuid": result['server_uuid'],
            "gateway_url": GATEWAY_URL,
            "streamable_http_endpoint": f"{GATEWAY_URL}/servers/{result['server_uuid']}/mcp",
            "tool_count": result['tool_count'],
            "api_name": result['api_name']
        }
        
        config_file = "mcp_server_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 Configuration saved to: {config_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
