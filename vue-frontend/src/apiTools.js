// import axios from 'axios';
//
// const fetchCameras = async () => {
//     try {
//         const response = await axios.get('/api/cameras');
//         if (response.data && Array.isArray(response.data)) {
//             return response.data;
//         } else {
//             console.error('Invalid response from server:', response);
//             return [];
//         }
//     } catch (error) {
//         if (error.response) {
//             // Server responded with a status other than 2xx
//             console.error('Server error:', error.response.status, error.response.data);
//         } else if (error.request) {
//             // Request was made but no response received
//             console.error('Network error:', error.request);
//         } else {
//             // Something else happened
//             console.error('Error:', error.message);
//         }
//         return [];
//     }
// }

// Dumb data
const fetchCameras = async () => {
    return [
        { index: 1, description: 'Front Door Camera', active: true, ip: '192.168.1.10' },
        { index: 2, description: 'Backyard Camera', active: false, ip: '192.168.1.11' },
    ];
}

export { fetchCameras };
