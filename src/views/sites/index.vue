<template>
  <div class="sites-page">
    <div class="page-header">
      <h2>Data Center Sites</h2>
      <el-button type="primary" @click="showDialog = true">
        <el-icon><Plus /></el-icon>
        Add Site
      </el-button>
    </div>

    <el-table :data="sites" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="Site Name" />
      <el-table-column prop="regionName" label="Region" />
      <el-table-column prop="siteType" label="Site Type">
        <template #default="scope">
          <el-tag>{{ scope.row.siteType }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="address" label="Address" />
      <el-table-column prop="createdAt" label="Created Date" width="180" />
      <el-table-column label="Actions" width="200">
        <template #default="scope">
          <el-button size="small" @click="editSite(scope.row)">Edit</el-button>
          <el-button size="small" type="danger" @click="deleteSite(scope.row)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="showDialog"
      :title="isEdit ? 'Edit Site' : 'Add New Site'"
      width="600"
    >
      <el-form :model="form" label-width="140px">
        <el-form-item label="Site Name" required>
          <el-input v-model="form.name" placeholder="Enter site name" />
        </el-form-item>
        <el-form-item label="Region" required>
          <el-select v-model="form.regionId" placeholder="Select region" style="width: 100%">
            <el-option
              v-for="region in regions"
              :key="region.id"
              :label="region.name"
              :value="region.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Site Type" required>
          <el-select v-model="form.siteType" placeholder="Select site type" style="width: 100%">
            <el-option label="Building" value="Building" />
            <el-option label="Shelter" value="Shelter" />
            <el-option label="Building + Shelters" value="Building + Shelters" />
          </el-select>
        </el-form-item>
        <el-form-item label="Address">
          <el-input
            v-model="form.address"
            type="textarea"
            :rows="2"
            placeholder="Enter site address"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveSite">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'Sites',
  data() {
    return {
      sites: [],
      regions: [],
      showDialog: false,
      isEdit: false,
      form: {
        id: null,
        name: '',
        regionId: '',
        siteType: '',
        address: ''
      }
    };
  },
  mounted() {
    this.loadData();
  },
  methods: {
    loadData() {
      this.regions = JSON.parse(localStorage.getItem('regions') || '[]');
      this.sites = JSON.parse(localStorage.getItem('sites') || '[]');
    },
    saveSite() {
      if (!this.form.name || !this.form.regionId || !this.form.siteType) {
        this.$message.error('Please fill in all required fields');
        return;
      }

      const region = this.regions.find(r => r.id === this.form.regionId);
      const siteData = {
        ...this.form,
        regionName: region ? region.name : ''
      };

      if (this.isEdit) {
        const index = this.sites.findIndex(s => s.id === this.form.id);
        if (index > -1) {
          this.sites[index] = siteData;
        }
      } else {
        this.sites.push({
          ...siteData,
          id: Date.now(),
          createdAt: new Date().toLocaleDateString()
        });
      }

      localStorage.setItem('sites', JSON.stringify(this.sites));
      this.showDialog = false;
      this.resetForm();
      this.$message.success('Site saved successfully');
    },
    editSite(site) {
      this.isEdit = true;
      this.form = { ...site };
      this.showDialog = true;
    },
    deleteSite(site) {
      this.$confirm('Are you sure to delete this site?', 'Warning', {
        confirmButtonText: 'OK',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }).then(() => {
        this.sites = this.sites.filter(s => s.id !== site.id);
        localStorage.setItem('sites', JSON.stringify(this.sites));
        this.$message.success('Site deleted successfully');
      }).catch(() => {});
    },
    resetForm() {
      this.form = {
        id: null,
        name: '',
        regionId: '',
        siteType: '',
        address: ''
      };
      this.isEdit = false;
    }
  }
}
</script>

<style scoped>
.sites-page {
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