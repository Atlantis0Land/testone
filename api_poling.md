## **Polling API - Example Implementation**


#### **Request:**
```bash
GET /api/alerts/new?since=2025-08-20T15:30:00Z&limit=10
Authorization: Bearer your_api_token_here
Content-Type: application/json
```

#### **Response:**
```json
{
  "success": true,
  "timestamp": "2025-08-20T15:35:00Z",
  "total_new_alerts": 2,
  "alerts": [
    {
      "id": "alert_001",
      "type": "SPEED_VIOLATION",
      "typeName": "Speed Violation",
      "content": "Vehicle exceeded speed limit in residential area",
      "address": "Al Nahda Street, Al Dhahira Governorate, Oman",
      "location": "23.7000,56.9000",
      "deviceCode": "ZNXLCWLB0001Oman",
      "deviceName": "Smart Patrol Vehicle Oman No.1",
      "gmtCreate": "2025-08-20T15:32:15Z",
      "pic": "https://example.com/alert1.jpg,https://example.com/alert2.jpg",
      "video": "https://example.com/violation.mp4"
    },
    {
      "id": "alert_002", 
      "type": "ILLEGAL_PARKING",
      "typeName": "Illegal Parking",
      "content": "Vehicle parked in no-parking zone",
      "address": "Sultan Qaboos Street, Muscat, Oman",
      "location": "23.7100,56.9100",
      "deviceCode": "ZNXLCWLB0001Oman",
      "deviceName": "Smart Patrol Vehicle Oman No.1",
      "gmtCreate": "2025-08-20T15:34:20Z",
      "pic": "https://example.com/parking1.jpg",
      "video": null
    }
  ],
  "next_since": "2025-08-20T15:35:00Z",
  "has_more": false
}
```



#### **请求：**
```bash
GET /api/alerts/new?since=2025-08-20T15:30:00Z&limit=10
Authorization: Bearer your_api_token_here
Content-Type: application/json
```

#### **响应：**
```json
{
  "success": true,
  "timestamp": "2025-08-20T15:35:00Z",
  "total_new_alerts": 2,
  "alerts": [
    {
      "id": "alert_001",
      "type": "SPEED_VIOLATION", 
      "typeName": "超速违规",
      "content": "车辆在住宅区超过限速",
      "address": "阿曼扎希拉省纳哈达街",
      "location": "23.7000,56.9000",
      "deviceCode": "ZNXLCWLB0001Oman",
      "deviceName": "阿曼智能巡逻车1号",
      "gmtCreate": "2025-08-20T15:32:15Z",
      "pic": "https://example.com/alert1.jpg,https://example.com/alert2.jpg",
      "video": "https://example.com/violation.mp4"
    },
    {
      "id": "alert_002",
      "type": "ILLEGAL_PARKING",
      "typeName": "违规停车", 
      "content": "车辆在禁停区域违规停车",
      "address": "阿曼马斯喀特苏丹卡布斯街",
      "location": "23.7100,56.9100", 
      "deviceCode": "ZNXLCWLB0001Oman",
      "deviceName": "阿曼智能巡逻车1号",
      "gmtCreate": "2025-08-20T15:34:20Z",
      "pic": "https://example.com/parking1.jpg",
      "video": null
    }
  ],
  "next_since": "2025-08-20T15:35:00Z",
  "has_more": false
}
```

### **Acknowledge Request:**
```bash
POST /api/alerts/acknowledge
Authorization: Bearer your_api_token_here
Content-Type: application/json

{
  "alert_ids": ["alert_001", "alert_002"],
  "acknowledged_at": "2025-08-20T15:35:30Z"
}
```
