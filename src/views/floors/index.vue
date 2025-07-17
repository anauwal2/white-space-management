// src/views/floors/index.vue 
<template>
  <div class="floors-page">
    <div class="page-header">
      <h2>Floors & Shelters</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>
        Add Floor/Shelter
      </el-button>
    </div>

    <el-table :data="floors" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="Name" />
      <el-table-column prop="siteName" label="Site" />
      <el-table-column prop="type" label="Type">
        <template #default="scope">
          <el-tag :type="scope.row.type === 'Floor' ? 'primary' : 'success'">
            {{ scope.row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Dimensions">
        <template #default="scope">
          {{ getGridDimensions(scope.row) }}
        </template>
      </el-table-column>
      <el-table-column label="Grid">
        <template #default="scope">
          {{ scope.row.gridSize }}cm
        </template>
      </el-table-column>
      <el-table-column prop="dcPowerCapacity" label="DC Power (kW)" />
      <el-table-column prop="acPowerCapacity" label="AC Power (kW)" />
      <el-table-column label="Actions" width="250">
        <template #default="scope">
          <el-button size="small" @click="editFloor(scope.row)">Edit</el-button>
          <el-button size="small" type="success" @click="openFloorPlan(scope.row)">Floor Plan</el-button>
          <el-button size="small" type="danger" @click="deleteFloor(scope.row)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="showDialog"
      :title="isEdit ? 'Edit Floor/Shelter' : 'Add New Floor/Shelter'"
      width="600"
    >
      <el-form :model="form" label-width="140px">
        <el-form-item label="Name" required>
          <el-input v-model="form.name" placeholder="Enter name" />
        </el-form-item>
        <el-form-item label="Site" required>
          <el-select v-model="form.siteId" placeholder="Select site" style="width: 100%">
            <el-option
              v-for="site in sites"
              :key="site.id"
              :label="site.name"
              :value="site.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Type" required>
          <el-radio-group v-model="form.type">
            <el-radio label="Floor">Floor</el-radio>
            <el-radio label="Shelter">Shelter</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-divider>Dimensions</el-divider>
        
        <el-form-item label="Width (Columns)">
          <el-input
            v-model="form.widthColumns"
            placeholder="Enter last column (e.g., AD)"
            style="width: 100%"
            @input="calculateWidthFromColumns"
          />
          <span class="form-hint">Enter the last column letter (AA, AB, AC, AD, etc.)</span>
        </el-form-item>
        
        <el-form-item label="Height (Rows)">
          <el-input-number
            v-model="form.heightRows"
            :min="10"
            :max="200"
            :step="1"
            placeholder="Number of rows"
            style="width: 100%"
            @input="calculateHeightFromRows"
          />
          <span class="form-hint">Enter the number of rows (e.g., 40 for rows 01-40)</span>
        </el-form-item>
        
        <el-form-item label="Grid Size">
          <el-input-number
            v-model="form.gridSize"
            :min="30"
            :max="120"
            :step="10"
            placeholder="cm"
            style="width: 100%"
          >
            <template #append>cm</template>
          </el-input-number>
          <span class="form-hint">Grid size for object placement (default: 60cm)</span>
        </el-form-item>
        
        <el-divider>Power Capacity</el-divider>
        
        <el-form-item label="DC Power Capacity">
          <el-input-number
            v-model="form.dcPowerCapacity"
            :min="0"
            :max="10000"
            placeholder="kW"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="AC Power Capacity">
          <el-input-number
            v-model="form.acPowerCapacity"
            :min="0"
            :max="10000"
            placeholder="kW"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialog">Cancel</el-button>
        <el-button type="primary" @click="saveFloor">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'Floors',
  data() {
    return {
      floors: [],
      sites: [],
      showDialog: false,
      isEdit: false,
      form: {
        id: null,
        name: '',
        siteId: '',
        type: 'Floor',
        width: 1200,
        height: 720,
        widthColumns: 'AA',
        heightRows: 12,
        gridSize: 60,
        dcPowerCapacity: 0,
        acPowerCapacity: 0
      }
    };
  },
  mounted() {
    this.loadData();
  },
  methods: {
    getGridDimensions(floor) {
      const width = floor.width || 1200;
      const height = floor.height || 720;
      const gridSize = floor.gridSize || 60;
      
      // Calculate number of grid columns and rows
      const cols = Math.floor(width / gridSize);
      const rows = Math.floor(height / gridSize);
      
      // Generate the last column letter using AA format
      const lastFirstLetter = Math.floor((cols - 1) / 26);
      const lastSecondLetter = (cols - 1) % 26;
      const lastColLetter = String.fromCharCode(65 + lastFirstLetter) + String.fromCharCode(65 + lastSecondLetter);
      
      // Format last row with leading zero
      const lastRowString = String(rows).padStart(2, '0');
      
      return `AA01 - ${lastColLetter}${lastRowString} (${width}cm × ${height}cm)`;
    },
    calculateWidthFromColumns() {
      const columns = this.form.widthColumns.toUpperCase();
      if (columns.length === 2) {
        // Double letter format: AA=1, AB=2, AC=3, etc.
        const firstLetter = columns.charCodeAt(0) - 65; // A=0, B=1, etc.
        const secondLetter = columns.charCodeAt(1) - 65; // A=0, B=1, etc.
        const colNumber = (firstLetter * 26) + secondLetter + 1;
        this.form.width = colNumber * this.form.gridSize;
      }
    },
    calculateHeightFromRows() {
      this.form.height = this.form.heightRows * this.form.gridSize;
    },
    columnsToNumber(columns) {
      const cols = columns.toUpperCase();
      if (cols.length === 2) {
        const firstLetter = cols.charCodeAt(0) - 65;
        const secondLetter = cols.charCodeAt(1) - 65;
        return (firstLetter * 26) + secondLetter + 1;
      }
      return 20; // default
    },
    numberToColumns(number) {
      const firstLetter = Math.floor((number - 1) / 26);
      const secondLetter = (number - 1) % 26;
      return String.fromCharCode(65 + firstLetter) + String.fromCharCode(65 + secondLetter);
    },
    loadData() {
      this.sites = JSON.parse(localStorage.getItem('sites') || '[]');
      const floorsData = JSON.parse(localStorage.getItem('floors') || '[]');
      
      // Migrate old data if needed
      this.floors = floorsData.map(floor => {
        if (!floor.width || !floor.height) {
          // Set default dimensions for old data
          return {
            ...floor,
            width: floor.width || 1200,
            height: floor.height || 720,
            gridSize: floor.gridSize || 60
          };
        }
        return floor;
      });
      
      // Save migrated data
      if (floorsData.some(floor => !floor.width || !floor.height)) {
        localStorage.setItem('floors', JSON.stringify(this.floors));
      }
    },
    saveFloor() {
      if (!this.form.name || !this.form.siteId) {
        this.$message.error('Please fill in all required fields');
        return;
      }

      const site = this.sites.find(s => s.id === this.form.siteId);
      const floorData = {
        ...this.form,
        siteName: site ? site.name : ''
      };

      if (this.isEdit) {
        const index = this.floors.findIndex(f => f.id === this.form.id);
        if (index > -1) {
          this.floors[index] = floorData;
        }
      } else {
        this.floors.push({
          ...floorData,
          id: Date.now(),
          createdAt: new Date().toLocaleDateString()
        });
      }

      localStorage.setItem('floors', JSON.stringify(this.floors));
      this.showDialog = false;
      this.resetForm();
      this.$message.success('Floor/Shelter saved successfully');
    },
    editFloor(floor) {
      this.isEdit = true;
      const width = floor.width || 1200;
      const height = floor.height || 720;
      const gridSize = floor.gridSize || 60;
      
      // Calculate columns and rows from pixel dimensions
      const cols = Math.floor(width / gridSize);
      const rows = Math.floor(height / gridSize);
      
      this.form = { 
        ...floor,
        width: width,
        height: height,
        gridSize: gridSize,
        widthColumns: this.numberToColumns(cols),
        heightRows: rows
      };
      this.showDialog = true;
    },
    deleteFloor(floor) {
      this.$confirm('Are you sure to delete this floor/shelter?', 'Warning', {
        confirmButtonText: 'OK',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }).then(() => {
        this.floors = this.floors.filter(f => f.id !== floor.id);
        localStorage.setItem('floors', JSON.stringify(this.floors));
        
        // Also delete associated floor plan
        const floorPlans = JSON.parse(localStorage.getItem('floorPlans') || '{}');
        if (floorPlans[floor.id]) {
          delete floorPlans[floor.id];
          localStorage.setItem('floorPlans', JSON.stringify(floorPlans));
        }
        
        this.$message.success('Floor/Shelter deleted successfully');
      }).catch(() => {});
    },
    openFloorPlan(floor) {
      this.$router.push(`/floor-plan/${floor.id}`);
    },
    cancelDialog() {
      this.showDialog = false;
      this.resetForm();
    },
    resetForm() {
      this.form = {
        id: null,
        name: '',
        siteId: '',
        type: 'Floor',
        width: 1200,
        height: 720,
        gridSize: 60,
        dcPowerCapacity: 0,
        acPowerCapacity: 0
      };
      this.isEdit = false;
    }
  }
}
</script>

<style scoped>
.floors-page {
  background: white;
  padding: 20px;
  border-radius: 4px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.el-divider {
  margin: 20px 0;
}
</style>