# API Documentation

## 1. Interface Signature Verification
All signature parameters need to be placed in the request header and must be included with each request.
Each partner will be assigned an AppKey and AppSecret.
Signature parameters:
- X-APP: Assigned AppKey
- X-TIME: Timestamp, using current time in milliseconds
- X-SIGN: Signature value, signing algorithm: md5Hex(AppKey + '&' + X-TIME + '&' + AppSecret)

## 2. API Endpoint
```
https://bike.lzyzn.net:9999/
```

## 3. Vehicle Information Data (License Plate, Type)
Request: GET `inspect/third-api/bikes`
Response:
```json
    {
        "code": 1, // Interface response status. Non-1 indicates failure
        "msg": "", // Error message. Present when code != 1
        "data": [
            {
                "id": 1, // Device ID
                "code": "DEV2023001", // Unique device code
                "name": "Smart Inspection Device 001", // Device name
                "pic": "https://example.com/device/DEV2023001.jpg", // Image URL
                "location": "120.00,30.11", // WGS84 coordinates
                "online": 1, // 0: offline, 1: online
                "gmtOnline": "2023-10-26 14:30:00", // Device online time
                "memberId": 1001, // Currently bound member ID
                "memberName": "Zhang San", // Currently bound member name
                "bindingTime": "2023-10-26 09:15:00", // Device binding time
                "number": "京A12345", // License plate number (may be empty)
                "patrolMode": 0 // Patrol mode: 0: QR code to start patrol, 1: Auto patrol on startup
            }
        ]
    }
```

## 4. Paginated Query of Vehicle Patrol Records
Request: GET `inspect/third-api/patrols`
Parameters:
- code: Device code, e.g., DEV2023001
- day: 2023-10-26 // Query date
- page: 1 // Page number
- pageSize: 20 // Records per page

Response:
```json
    {
        "code": 1, // Interface response status. Non-1 indicates failure
        "msg": "", // Error message. Present when code != 1
        "total": 100, // Total records count for pagination
        "data": [
            {
                "id": 1001, // Patrol record ID
                "deviceCode": "DEV2023001", // Device code
                "deviceName": "Smart Inspection Device 001", // Device name
                "tenantId": 10001, // Tenant ID
                "memberId": 2001, // Inspector ID
                "memberName": "Zhang San", // Inspector name
                "startTime": "2023-10-26 09:00:00", // Patrol start time
                "status": 0, // Patrol status: 0-ended, 1-in progress
                "endTime": "2023-10-26 11:30:00", // Patrol end time
                "patrolSum": 9000, // Patrol duration (seconds)
                "warningSum": 3, // Event count (related to warnings) 
                "gmtModified": "2023-10-26 11:30:00" // Record update time
            }
        ]
    }
```

## 5. Query Location List by Patrol Record
Request: GET `inspect/third-api/locations`
Parameters:
- patrolId: Patrol record ID

Response:
```json
    {
        "code": 1, // Interface response status. Non-1 indicates failure
        "msg": "", // Error message. Present when code != 1
        "data": [
            {
                "id": 1001, // Primary key ID
                "patrolRecordId": 2001, // Patrol record ID
                "deviceCode": "DEV2023001", // Device code
                "deviceName": "Smart Inspection Device 001", // Device name
                "location": "120.000,30.011" // Collected location information
            }
        ]
    }
```

## 6. Vehicle Camera List Query
Some vehicle models may have multiple monitors.
Request: GET `inspect/third-api/deviceMonitors`
Parameters:
- code: Vehicle device code

Response:
```json
    {
        "code": 1, // Interface response status. Non-1 indicates failure
        "msg": "", // Error message. Present when code != 1
        "data": [
            {
                "id": 1001, // Primary key ID
                "code": 3301102001020100210, // National standard code for vehicle monitor
                "position": "Front" // Monitor position name
            }
        ]
    }
```

## 7. Get Video Stream URL by Camera Code
Request: GET `inspect/monitor/video?code=3301102001020100210`
Response:
```json
    {
        "code": 1,
        "msg": "",
        "data": {
            "stream": "stream_20231026_001", // Stream ID
            "name": "Camera 001", // Channel name
            "channel": "34020000001320000001", // Channel ID
            "flv": "http://192.168.1.100:8091/rtp/stream_20231026_001.live.flv", // FLV stream URL
            "hls": "http://192.168.1.100:8091/rtp/stream_20231026_001/hls.m3u8", // HLS stream URL
            "https_flv": "https://video.example.com/rtp/stream_20231026_001.live.flv", // HTTPS FLV stream URL
            "https_hls": "https://video.example.com/rtp/stream_20231026_001/hls.m3u8" // HTTPS HLS stream URL
        }
    }
```

## 8. Query All Attendance Personnel
Request: GET `workbench/api/members`
Parameters: None
Response:
```json
    {
        "code": 1,
        "msg": null,
        "data": [
            {
                "id": 152,
                "memberId": 143,
                "memberCode": "1009",
                "memberName": "Zhang Min",
                "groupId": 71,
                "groupName": "Sanitation Department",
                "groupPath": "63/71/",
                "tenantId": 40,
                "teamId": 53,
                "teamName": "Sanitation Department",
                "cardNum": "868120321297951", // Employee card number
                "online": 1, // 0: offline, 1: online
                "lastLocation": "120.000,32.0000", // Last attendance location
                "lastClockIn": null,
                "lastClockOut": null,
                "clockStatus": 0,
                "type": 1
            }
        ]
    }
```

## 9. Fixed Camera List
Request: GET `workbench/api/monitors`
Parameters: None
Response:
```json
    {
        "code": 1,
        "msg": "",
        "data": [
            {
                "id": 1,
                "name": "Fixed Camera 001",
                "code": "DJK001", // Fixed Camera code, used to get video stream
                "location": "120.000,30.011", // WGS84 coordinates
                "status": 1 // 0: offline, 1: online
            }
        ]
    }
```

## 10. Get Fixed Camera Video Stream URL
Request: GET `/monitor/monitor/video?code=DJK001&type=flv`
Parameters:
- code: DJK001 // Fixed Camera code
- type: flv // Currently only supports flv

Response:
```json
    {
        "code": 1,
        "msg": null,
        "data": {
            "code": "DJK001",
            "name": "Dam Office Behind Garbage Station (Public Toilet) Camera",
            "type": 0, // 0: unknown, 1: bullet camera, 2: PTZ camera
            "src": "https://api.lzyzn.net:8888/flv?app=live&stream=178667cd67ce909faab25258d32f94ce"
        }
    }
```


11. Patrol Warning Push
    Customers need to implement an interface to receive push data, and set the push address, warning types to push, and push method in the web console. 
    When patrol devices detect warnings and report them to the system, the system pushes data to the customer's platform through configured push settings.
    Receiving push data does not require signature verification.
    - Push Address: HTTP address provided by the customer
    - HTTP Method for Push: POST
    - Push Example:
```json
    {
        "id": "1",  // Warning ID
        "patrolRecordId": 1,  // Patrol record ID
        "code": "SDZP20240914171743798", // Warning code
        "type": "LMJS", // Warning type code
        "typeName": "路面积水", // Warning type name (Road Water Accumulation)
        "content": "问题描述",  // Warning content (Problem Description)
        "pic": "simple/202311/14/14/c17301b4a2164.jpg,simple/202311/14/14/c17301b4a2162.jpg", // Image addresses, multiple separated by commas
        "address": "浙江省杭州市余杭区五常街道江南水乡(东1门)", // Warning address (Jiangnan Shuixiang, Wuchang Street, Yuhang District, Hangzhou City, Zhejiang Province (East Gate 1))
        "location": "120.202526,30.337866", // Warning location WGS84
        "deviceCode": "ZNXLCWLB0001", // Patrol device code
        "deviceName": "智能巡逻车1号", // Patrol device name (Smart Patrol Vehicle No. 1)
        "gmtCreate": "2024-08-02 19:26:16", // Warning creation time  
        "video": "simple/202409/14/17/ae83697e2510e14835017f3c.mp4" // A video segment when the warning occurred
    }
```

12. Fetch new  Warning  
    Request: GET /inspect/third-api/warning/new 
    Parameters:
      - limit: Number of warnings to retrieve, default 20, maximum 1000 
    Response:
```json
{
  "code": 1,
  "msg": "",
  "data": [
    {
      "id": "1", // Warning ID
      "patrolRecordId": 1, // Patrol record ID
      "code": "SDZP20240914171743798", // Warning code
      "type": "LMJS", // Warning type code
      "typeName": "Road Waterlogging", // Warning type name
      "content": "Problem description", // Warning content
      "pic": "simple/202311/14/14/c17301b4a2164.jpg,simple/202311/14/14/c17301b4a2162.jpg", // Image addresses, separated by commas
      "address": "East Gate of Jiangnan Shui Xiang, Wuchang Street, Yuhang District, Hangzhou City, Zhejiang Province", // Warning address
      "location": "120.202526,30.337866", // Warning location WGS84
      "deviceCode": "ZNXLCWLB0001", // Patrol device code
      "deviceName": "Intelligent Patrol Vehicle No.1", // Patrol device name
      "gmtCreate": "17278898888", // Warning generation time in milliseconds
      "video": "simple/202409/14/17/ae83697e2510e14835017f3c.mp4" // Video clip when the warning occurred
    }
  ]
}
```

13. Notify Warning Processing Completion
    Request: POST /inspect/third-api/warning/ack
    Parameters:
```json
{
  "ids": [1,2,3]  // Warning IDs
}
```
    Response:
```json
{
  "code": 1,
  "msg": ""
}
```
