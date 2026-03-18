// API Client for SK Manager Backend

// In development, this points to your API Gateway Invoke URL once deployed
// We'll leave it empty for now, or you can hardcode the URL from 'terraform output'
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:3000' // For local mocking if needed later
    : 'https://3tl7exskh7.execute-api.eu-north-1.amazonaws.com/v1'; // Production API Gateway URL

class API {
    static async request(endpoint, method = 'GET', body = null) {
        if (!API_BASE_URL) {
            console.warn(`API_BASE_URL is not set. Assuming local mock for ${method} ${endpoint}`);
            return this.mockResponse(endpoint, method, body);
        }

        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        if (body && method !== 'GET') {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            console.log(`API Response: ${response.status} ${response.statusText} for ${method} ${endpoint}`);
            
            const data = await response.json().catch(() => ({}));
            
            if (!response.ok) {
                console.error(`API Error details for ${method} ${endpoint}:`, data);
                throw new Error(data.error || `API Request Failed with status ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error(`API Error on ${method} ${endpoint}:`, error);
            throw error;
        }
    }

    // --- Equipment CRUD ---
    
    static async getEquipment() {
        return this.request('/equipment');
    }

    static async getEquipmentDetails(id) {
        return this.request(`/equipment/${id}`);
    }

    static async createEquipment(data) {
        return this.request('/equipment', 'POST', data);
    }

    static async updateEquipment(id, data) {
        return this.request(`/equipment/${id}`, 'PUT', data);
    }

    static async deleteEquipment(id) {
        return this.request(`/equipment/${id}`, 'DELETE');
    }

    // --- Lending System ---
    
    static async getActiveLendings() {
        return this.request('/lendings');
    }

    static async lendItem(id, borrower, quantity) {
        return this.request(`/equipment/${id}/lend`, 'POST', { borrower, quantity });
    }

    static async returnItem(equipmentId, lendingId) {
        return this.request(`/equipment/${equipmentId}/return`, 'POST', { lending_id: lendingId });
    }

    // --- Photos ---
    
    static async getPhotoUploadUrl(equipmentId, contentType) {
        return this.request(`/equipment/${equipmentId}/photo`, 'POST', { content_type: contentType });
    }

    static async uploadPhotoToS3(uploadUrl, file) {
        try {
            const response = await fetch(uploadUrl, {
                method: 'PUT',
                body: file,
                headers: {
                    'Content-Type': file.type
                }
            });
            if (!response.ok) throw new Error("Failed to upload to S3");
            return true;
        } catch (error) {
            console.error("S3 Upload Error:", error);
            throw error;
        }
    }

    // --- History ---
    
    static async getHistory(equipmentId) {
        return this.request(`/equipment/${equipmentId}/history`);
    }

    // --- MOCK RESPONSES FOR DEVELOPMENT PREVIEW ---
    static async mockResponse(endpoint, method, body) {
        return new Promise((resolve) => {
            setTimeout(() => {
                if (endpoint === '/equipment' && method === 'GET') {
                    resolve([
                        { equipment_id: '1', name: 'Basketball (Spalding)', category: 'Balls', quantity: 15, location: 'Shed A - Shelf 2', photo_url: '' },
                        { equipment_id: '2', name: 'Tennis Rackets', category: 'Rackets', quantity: 8, location: 'Shed B - Shelf 1', photo_url: '' },
                        { equipment_id: '3', name: 'Training Cones', category: 'Cones', quantity: 50, location: 'Shed A - Floor', photo_url: '' }
                    ]);
                } else if (endpoint === '/lendings' && method === 'GET') {
                    resolve([
                        { lending_id: 'L1', equipment_id: '1', borrower: 'John Doe', quantity: 2, lent_date: new Date().toISOString() },
                        { lending_id: 'L2', equipment_id: '2', borrower: 'Jane Smith', quantity: 4, lent_date: new Date().toISOString() }
                    ]);
                } else {
                    resolve({ success: true, message: "Mock operation successful", data: body });
                }
            }, 500); // Simulate network latency
        });
    }
}
