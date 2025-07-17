<template>
  <div class="regions-page">
    <div class="page-header">
      <h2>Regions Management</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>
        Add Region
      </el-button>
    </div>

    <el-table :data="regions" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="Region Name" />
      <el-table-column prop="description" label="Description" />
      <el-table-column prop="createdAt" label="Created Date" width="180" />
      <el-table-column label="Actions" width="200">
        <template #default="scope">
          <el-button size="small" @click="editRegion(scope.row)">Edit</el-button>
          <el-button size="small" type="danger" @click="deleteRegion(scope.row)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="showDialog"
      :title="isEdit ? 'Edit Region' : 'Add New Region'"
      width="500"
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="Region Name" required>
          <el-input v-model="form.name" placeholder="Enter region name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="Enter description"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveRegion">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'Regions',
  data() {
    return {
      regions: [],
      showDialog: false,
      isEdit: false,
      form: {
        id: null,
        name: '',
        description: ''
      }
    };
  },
  mounted() {
    this.loadRegions();
  },
  methods: {
    loadRegions() {
      this.regions = JSON.parse(localStorage.getItem('regions') || '[]');
    },
    saveRegion() {
      if (!this.form.name) {
        this.$message.error('Please enter region name');
        return;
      }

      if (this.isEdit) {
        const index = this.regions.findIndex(r => r.id === this.form.id);
        if (index > -1) {
          this.regions[index] = { ...this.form };
        }
      } else {
        this.regions.push({
          ...this.form,
          id: Date.now(),
          createdAt: new Date().toLocaleDateString()
        });
      }

      localStorage.setItem('regions', JSON.stringify(this.regions));
      this.showDialog = false;
      this.resetForm();
      this.$message.success('Region saved successfully');
    },
    editRegion(region) {
      this.isEdit = true;
      this.form = { ...region };
      this.showDialog = true;
    },
    deleteRegion(region) {
      this.$confirm('Are you sure to delete this region?', 'Warning', {
        confirmButtonText: 'OK',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }).then(() => {
        this.regions = this.regions.filter(r => r.id !== region.id);
        localStorage.setItem('regions', JSON.stringify(this.regions));
        this.$message.success('Region deleted successfully');
      }).catch(() => {});
    },
    resetForm() {
      this.form = {
        id: null,
        name: '',
        description: ''
      };
      this.isEdit = false;
    }
  }
}
</script>

<style scoped>
.regions-page {
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
</style>