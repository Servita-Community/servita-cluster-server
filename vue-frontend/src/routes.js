import Home from './components/HomeComponent.vue';
import Streams from './components/StreamsComponent.vue';
import Settings from './components/SettingsComponent.vue';
import FleetManagement from './components/FleetManagementComponent.vue';

const routes = [
    { name: 'Home', path: '/', component: Home },
    { name: 'Streams', path: '/streams', component: Streams, icon: 'mdi-video' },
    { name: 'Settings', path: '/settings', component: Settings, icon: 'mdi-cog' },
    { name: 'Fleet Management', path: '/fleetmanagement', component: FleetManagement, icon: 'mdi-truck' },
];

export default routes;
