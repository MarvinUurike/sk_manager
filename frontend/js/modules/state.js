export const state = {
    equipment: [],
    lendings: [],
    filter: 'all',
    searchTerm: '',

    setEquipment(data) {
        this.equipment = data;
    },

    setLendings(data) {
        this.lendings = data;
    },

    setFilter(filter) {
        this.filter = filter;
    },

    setSearchTerm(term) {
        this.searchTerm = term.toLowerCase();
    },

    getLentQuantity(equipmentId) {
        return this.lendings
            .filter(l => l.equipment_id === equipmentId)
            .reduce((sum, loan) => sum + parseInt(loan.quantity), 0);
    },

    getFilteredData() {
        return this.equipment.filter(item => {
            const matchesSearch = item.name.toLowerCase().includes(this.searchTerm) || 
                                item.category.toLowerCase().includes(this.searchTerm);
            
            const total = parseInt(item.quantity);
            const lent = this.getLentQuantity(item.id || item.equipment_id);
            const available = total - lent;
            
            if (this.filter === 'available') return matchesSearch && available > 0;
            if (this.filter === 'lent') return matchesSearch && lent > 0;
            return matchesSearch;
        });
    }
};
