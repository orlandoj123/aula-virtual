// App.js - Lógica de la aplicación
function logout() {
    localStorage.clear();
    window.location.href = '/login';
}
