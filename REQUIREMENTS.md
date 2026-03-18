# SK Manager — Sports Club Equipment Management

## Project Overview

**SK Manager** is a sports club management tool. The first iteration focuses on **equipment storage and lending** — tracking what equipment the club owns, where it's stored, and who currently has it checked out.

---

## Goals

1. Provide a clear overview of all sports equipment owned by the club
2. Track the physical storage location of each item
3. Track lending — show who has borrowed an item and when
4. Keep it simple, easy to use, and easy to maintain

---

## Key Features (v1)

### Equipment Inventory
- List all equipment with name and quantity
- Show the storage location for each item (e.g., "Shed A — Shelf 3")
- Upload and display photos of each item (stored in S3)

### Lending System
- Check out an item to a club member
- Check in an item when returned
- View current status of any item:
  - **In stock** → show storage location
  - **Lent out** → show who has it and since when

### Dashboard
- At-a-glance overview of all equipment and their statuses
- Quick filters: all items, available, lent out

### History
- List all equipment and their lending history
- Quick filters: all items, available, lent out

---

## Tech Stack

| Layer          | Technology                     | Rationale                          |
|----------------|--------------------------------|------------------------------------|
| **Cloud**      | AWS                            | Required                           |
| **IaC**        | Terraform                      | Required                           |
| **Backend**    | AWS Lambda (Python)            | Serverless, simple, low cost       |
| **API**        | API Gateway (REST)             | Managed API layer for Lambda       |
| **Database**   | DynamoDB                       | Serverless NoSQL, simple key-value |
| **History**    | PostgreSQL (AWS RDS)           | Relational DB for audit & history  |
| **Frontend**   | EC2 (Nginx)                    | Hosted on `awsa-rds` instance      |
| **Storage**    | S3 (Photos bucket)             | Equipment photo storage            |
| **Auth**       | *(TBD — v2 or simple API key)* | Keep v1 simple                     |

---

## AWS Architecture (v1)

```
┌────────────┐     ┌──────────────┐     ┌────────────┐     ┌───────────────┐
│  Browser   │────▶│  EC2 Instance│────▶│  S3 Bucket │     │               │
│ (Frontend) │     │ ("awsa-rds") │     │  (Photos)  │     │   DynamoDB    │
└────────────┘     └──────────────┘     └────────────┘     │ (Live State)  │
      │                   │                                 └───────────────┘
      │                   ▼                 ┌────────────┐           ▲
      │            ┌──────────────┐         │  Lambda    │───────────┘
      └───────────▶│ API Gateway  │────────▶│  (Python)  │           ▼
                   │   (REST)     │         └─────┬──────┘     ┌───────────────┐
                   └──────────────┘               │            │               │
                                            ┌─────▼──────┐     │   PostgreSQL  │
                                            │ EventBridge│     │ (History/Logs)│
                                            │ (Scheduler)│     └───────────────┘
                                            └────────────┘
```

---

## Data Model

### Equipment Table
| Field          | Type   | Description                        |
|----------------|--------|------------------------------------|
| `equipment_id` | String | Primary key (UUID)                 |
| `name`         | String | Equipment name                     |
| `quantity`     | Number | Total quantity owned               |
| `location`     | String | Storage location when in stock     |
| `photo_url`    | String | S3 URL of equipment photo (optional)|

### Lending Table
| Field          | Type   | Description                        |
|----------------|--------|------------------------------------|
| `lending_id`   | String | Primary key (UUID)                 |
| `equipment_id` | String | FK → Equipment                     |
| `borrower`     | String | Name of the person borrowing       |
| `lent_date`    | String | ISO date when lent out             |
| `returned_date`| String | ISO date when returned (nullable)  |
| `quantity`     | Number | How many units lent                |

### History (PostgreSQL)
The relational database tracks every change for auditing and history.

#### `equipment_history`
- `id` (Serial, PK)
- `equipment_id` (FK)
- `action_type` (e.g., CREATE, UPDATE, DELETE)
- `timestamp`

#### `lending_history`
- `id` (Serial, PK)
- `lending_id` (FK)
- `action_type` (e.g., LEND, RETURN)
- `borrower`
- `timestamp`

---

## Terraform Structure (Planned)

```
terraform/
├── main.tf            # Provider config, backend
├── dynamodb.tf        # DynamoDB tables
├── lambda.tf          # Lambda functions + IAM roles
├── api_gateway.tf     # API Gateway setup
├── s3.tf              # S3 buckets (frontend + photos)
├── cloudfront.tf      # CloudFront distribution
├── variables.tf       # Input variables
└── outputs.tf         # Output values (URLs, etc.)
```

---

## API Endpoints (Planned)

| Method | Endpoint                | Description               |
|--------|-------------------------|---------------------------|
| GET    | `/equipment`            | List all equipment        |
| POST   | `/equipment`            | Add new equipment         |
| GET    | `/equipment/{id}`       | Get single item           |
| PUT    | `/equipment/{id}`       | Update an item            |
| DELETE | `/equipment/{id}`       | Delete an item            |
| POST   | `/equipment/{id}/lend`  | Lend out an item          |
| POST   | `/equipment/{id}/return`| Return a lent item        |
| POST   | `/equipment/{id}/photo` | Get presigned upload URL  |
| DELETE | `/equipment/{id}/photo` | Delete equipment photo    |
| GET    | `/lendings`             | List all active lendings  |

---

## Out of Scope (v1)

- User authentication / login
- Role-based access control
- Notifications or reminders for overdue items
- Mobile app
- Multi-club / multi-tenant support
- Equipment maintenance tracking

---

## Future Iterations

- **v2**: Authentication (Cognito), member management, overdue alerts
- **v3**: Reporting/analytics, equipment condition tracking, calendar integration
