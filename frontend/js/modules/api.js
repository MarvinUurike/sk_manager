const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/v1'
    : 'https://63u25w4rxl.execute-api.eu-north-1.amazonaws.com/v1';

export const API = {
    async getEquipment() {
        const res = await fetch(`${API_BASE_URL}/equipment`);
        if (!res.ok) throw new Error("Failed to fetch equipment");
        return res.json();
    },

    async getActiveLendings() {
        const res = await fetch(`${API_BASE_URL}/lendings`);
        if (!res.ok) throw new Error("Failed to fetch lendings");
        return res.json();
    },

    async createEquipment(data) {
        const res = await fetch(`${API_BASE_URL}/equipment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to create equipment");
        return res.json();
    },

    async updateEquipment(id, data) {
        const res = await fetch(`${API_BASE_URL}/equipment/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to update equipment");
        return res.json();
    },

    async getPhotoUploadUrl(id, contentType) {
        const res = await fetch(`${API_BASE_URL}/photos/upload-url?id=${id}&content_type=${contentType}`);
        if (!res.ok) throw new Error("Failed to get upload URL");
        return res.json();
    },

    async uploadPhotoToS3(url, file) {
        const res = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: { 'Content-Type': file.type }
        });
        if (!res.ok) throw new Error("Photo upload to S3 failed");
        return true;
    },

    async lendItem(equipmentId, borrower, quantity) {
        const res = await fetch(`${API_BASE_URL}/lendings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipment_id: equipmentId, borrower, quantity })
        });
        if (!res.ok) throw new Error("Lending failed");
        return res.json();
    },

    async returnItem(equipmentId, lendingId) {
        const res = await fetch(`${API_BASE_URL}/lendings/return`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equipment_id: equipmentId, lending_id: lendingId })
        });
        if (!res.ok) throw new Error("Return failed");
        return res.json();
    },

    async getHistory(equipmentId) {
        const res = await fetch(`${API_BASE_URL}/history?id=${equipmentId}`);
        if (!res.ok) throw new Error("Failed to fetch history");
        return res.json();
    }
};
