**Implementation Plan: Geolocation-based Matching**

**Key Steps:**
1. Add latitude/longitude fields to user profiles
2. Implement distance calculation algorithm (Haversine formula)
3. Create configurable radius parameter
4. Build compatibility scoring system
5. Develop sorting functionality by distance and compatibility

**Files to Create/Modify:**
- `user_model.py` (add geolocation fields)
- `matching_service.py` (distance/compatibility logic)
- `config.py` (radius settings)
- `api/endpoints.py` (matching endpoints)

**Dependencies:**
- `geopy` (distance calculations)
- `sqlalchemy` (database operations)
- `numpy` (compatibility scoring)
- `flask