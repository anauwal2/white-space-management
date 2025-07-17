import { createRouter, createWebHashHistory } from "vue-router";
import Dashboard from "../views/dashboard/index.vue";
import Regions from "../views/regions/index.vue";
import Sites from "../views/sites/index.vue";
import Floors from "../views/floors/index.vue";
import FloorPlan from "../views/floor-plan/index.vue";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: "/",
      redirect: "/dashboard"
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: Dashboard
    },
    {
      path: "/regions",
      name: "regions",
      component: Regions
    },
    {
      path: "/sites",
      name: "sites",
      component: Sites
    },
    {
      path: "/floors",
      name: "floors",
      component: Floors
    },
    {
      path: "/floor-plan/:id",
      name: "floor-plan",
      component: FloorPlan
    },
    {
      path: "/floor-plan-new/:id",
      name: "floor-plan-new",
      component: FloorPlan
    }
  ]
});

export default router;