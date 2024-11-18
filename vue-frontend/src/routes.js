import Home from './components/HomeComponent.vue';
import Settings from './components/SettingsComponent.vue';
import PanelStreams from './components/PanelStreamsComponent.vue';

const routes = [
    { name: 'Home', path: '/', component: Home },
    { name: 'Streams Panel', path: '/panelstreams', component: PanelStreams, icon: 'mdi-solar-panel-large' },
    { name: 'Settings', path: '/settings', component: Settings, icon: 'mdi-cog' },
];

export default routes;
