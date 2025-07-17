<template>
  <div class="dashboard">
    <h2>Dashboard</h2>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <el-statistic title="Total Regions" :value="statistics.regions" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="Total Sites" :value="statistics.sites" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="Total Floors" :value="statistics.floors" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="Total Power Capacity (AC + DC)" :value="statistics.totalCapacity" suffix="kW" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'Dashboard',
  data() {
    return {
      statistics: {
        regions: 0,
        sites: 0,
        floors: 0,
        totalCapacity: 0
      }
    };
  },
  mounted() {
    this.loadStatistics();
  },
  methods: {
    loadStatistics() {
      // Load from localStorage
      const regions = JSON.parse(localStorage.getItem('regions') || '[]');
      const sites = JSON.parse(localStorage.getItem('sites') || '[]');
      const floors = JSON.parse(localStorage.getItem('floors') || '[]');
      
      this.statistics.regions = regions.length;
      this.statistics.sites = sites.length;
      this.statistics.floors = floors.length;
      this.statistics.totalCapacity = floors.reduce((sum, floor) => {
        return sum + (floor.dcPowerCapacity || 0) + (floor.acPowerCapacity || 0);
      }, 0);
    }
  }
}
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
}
</style>