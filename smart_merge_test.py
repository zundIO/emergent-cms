#!/usr/bin/env python3
"""
Targeted test for the smart merge timestamp fix
Tests the specific scenario where CMS edits should be preserved
"""
import requests
import json
import time
from datetime import datetime, timezone, timedelta

BASE_URL = "https://page-studio-71.preview.emergentagent.com"

def test_smart_merge_fix():
    """Test the critical smart merge timestamp comparison fix"""
    print("🔍 Testing Smart Merge Timestamp Fix...")
    
    # Login as admin
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@monolith.cms",
        "password": "admin123"
    })
    
    if login_response.status_code != 200:
        print("❌ Admin login failed")
        return False
    
    token = login_response.json()['token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Step 1: Import initial schema with old timestamp
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    print(f"📅 Using old source timestamp: {old_timestamp}")
    
    initial_schema = {
        "project_name": "Smart Merge Test",
        "source_updated_at": old_timestamp,
        "pages": [{
            "name": "Test Page",
            "slug": "/test",
            "elements": [{
                "id": "test-element",
                "type": "heading",
                "tag": "h1",
                "label": "Test Element",
                "content": {"text": "Original Schema Text"},
                "style": {"classes": "text-4xl"},
                "children": []
            }]
        }]
    }
    
    import_response = requests.post(f"{BASE_URL}/api/projects/import", 
                                   json=initial_schema, headers=headers)
    
    if import_response.status_code != 200:
        print(f"❌ Initial schema import failed: {import_response.status_code}")
        return False
    
    project_id = import_response.json()['project_id']
    print(f"✅ Initial schema imported, project_id: {project_id}")
    
    # Step 2: Get the page ID
    pages_response = requests.get(f"{BASE_URL}/api/pages?project_id={project_id}", 
                                 headers=headers)
    
    if pages_response.status_code != 200:
        print("❌ Failed to get pages")
        return False
    
    pages = pages_response.json()
    if not pages:
        print("❌ No pages found")
        return False
    
    page_id = pages[0]['_id']
    print(f"✅ Found page ID: {page_id}")
    
    # Step 3: Edit content via CMS (this should get a newer timestamp)
    time.sleep(1)  # Ensure timestamp difference
    cms_edit_time = datetime.now(timezone.utc)
    print(f"📝 Making CMS edit at: {cms_edit_time.isoformat()}")
    
    edit_response = requests.put(f"{BASE_URL}/api/pages/{page_id}/content",
                                json={
                                    "element_id": "test-element",
                                    "content": {"text": "EDITED BY CMS - Should be preserved"}
                                }, headers=headers)
    
    if edit_response.status_code != 200:
        print(f"❌ CMS edit failed: {edit_response.status_code}")
        return False
    
    print("✅ CMS edit completed")
    
    # Step 4: Re-import schema with timestamp OLDER than CMS edit
    time.sleep(1)  # Ensure timestamp difference
    reimport_timestamp = (cms_edit_time - timedelta(minutes=30)).isoformat()
    print(f"📅 Re-importing with older timestamp: {reimport_timestamp}")
    
    reimport_schema = {
        "project_name": "Smart Merge Test",
        "source_updated_at": reimport_timestamp,  # This is OLDER than CMS edit
        "pages": [{
            "name": "Test Page",
            "slug": "/test",
            "elements": [{
                "id": "test-element",
                "type": "heading",
                "tag": "h1",
                "label": "Test Element",
                "content": {"text": "New Schema Text - Should NOT overwrite CMS"},
                "style": {"classes": "text-6xl"},  # Style should update
                "children": []
            }]
        }]
    }
    
    reimport_response = requests.post(f"{BASE_URL}/api/projects/import",
                                     json=reimport_schema, headers=headers)
    
    if reimport_response.status_code != 200:
        print(f"❌ Re-import failed: {reimport_response.status_code}")
        return False
    
    print("✅ Schema re-imported")
    
    # Step 5: Check the result
    page_response = requests.get(f"{BASE_URL}/api/pages/{page_id}", headers=headers)
    
    if page_response.status_code != 200:
        print("❌ Failed to get updated page")
        return False
    
    page_data = page_response.json()
    elements = page_data.get('elements', [])
    test_element = next((el for el in elements if el.get('id') == 'test-element'), None)
    
    if not test_element:
        print("❌ Test element not found")
        return False
    
    content_text = test_element.get('content', {}).get('text', '')
    style_classes = test_element.get('style', {}).get('classes', '')
    
    print(f"📄 Final content text: {content_text}")
    print(f"🎨 Final style classes: {style_classes}")
    
    # Verify results
    content_preserved = "EDITED BY CMS" in content_text
    style_updated = "text-6xl" in style_classes
    
    print(f"✅ Content preserved: {content_preserved}")
    print(f"✅ Style updated: {style_updated}")
    
    if content_preserved and style_updated:
        print("🎉 SMART MERGE FIX WORKING CORRECTLY!")
        return True
    else:
        print("❌ SMART MERGE FIX NOT WORKING")
        if not content_preserved:
            print("   - CMS content was overwritten (BUG)")
        if not style_updated:
            print("   - Style was not updated")
        return False

if __name__ == "__main__":
    success = test_smart_merge_fix()
    exit(0 if success else 1)