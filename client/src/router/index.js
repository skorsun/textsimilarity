import Vue from 'vue';
import VueRouter from 'vue-router';
import Texts from '../components/Texts.vue';
import Ping from '../components/Ping.vue';

Vue.use(VueRouter);

const routes = [
  {
    path: '/ping',
    name: 'ping',
    component: Ping,
  },
  {
    path: '/',
    name: 'texts',
    component: Texts,
  },
];

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
});

export default router;
