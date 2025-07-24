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
        type: 'Floor'
      }
    };
  },
  mounted() {
    this.loadData();
  },
  methods: {
    loadData() {
      this.sites = JSON.parse(localStorage.getItem('sites') || '[]');
      this.floors = JSON.parse(localStorage.getItem('floors') || '[]').map(floor => {
        const site = this.sites.find(s => s.id === floor.siteId);
        return {
          ...floor,
          siteName: site ? site.name : ''
        };
      });
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
      this.form = { ...floor };
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
        type: 'Floor'
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