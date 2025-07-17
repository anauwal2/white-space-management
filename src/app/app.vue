<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1 class="app-title">White Space Management</h1>
      <nav class="app-nav">
        <router-link to="/dashboard" class="nav-item" :class="{ active: $route.path === '/dashboard' }">
          <el-icon><Monitor /></el-icon>
          Dashboard
        </router-link>
        <router-link to="/regions" class="nav-item" :class="{ active: $route.path === '/regions' }">
          <el-icon><Location /></el-icon>
          Regions
        </router-link>
        <router-link to="/sites" class="nav-item" :class="{ active: $route.path === '/sites' }">
          <el-icon><OfficeBuilding /></el-icon>
          Data Centers
        </router-link>
        <router-link to="/floors" class="nav-item" :class="{ active: $route.path === '/floors' }">
          <el-icon><Grid /></el-icon>
          Floors/Shelters
        </router-link>
      </nav>
    </el-header>
    <el-main class="app-main">
      <router-view></router-view>
    </el-main>
  </el-container>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
.app-container {
  height: 100vh;
  background-color: #f5f7fa;
}

.app-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.app-title {
  margin: 0;
  font-size: 20px;
  color: #303133;
  white-space: nowrap;
}

.app-nav {
  display: flex;
  align-items: center;
  gap: 5px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 16px;
  color: #606266;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s;
  font-size: 14px;
  white-space: nowrap;
}

.nav-item:hover {
  background-color: #f5f7fa;
  color: #409eff;
}

.nav-item.active {
  color: #409eff;
  background-color: #ecf5ff;
}

.nav-item .el-icon {
  font-size: 16px;
}

.app-main {
  padding: 20px;
}
</style>