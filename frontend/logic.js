// logic.js
function validarPlaca(placa) {
    // Elimina guiones y espacios para la validación interna
    const placaLimpia = placa.replace(/[-\s]/g, '');
    // Expresión regular: 6 a 10 caracteres alfanuméricos
    const regex = /^[A-Za-z0-9]{6,10}$/;
    return regex.test(placaLimpia);
}

function calcularTarifa(horasEstadia) {
    const tarifaPorHora = 5.00;
    return Math.max(1, Math.ceil(horasEstadia)) * tarifaPorHora;
}

// Exportar para que Mocha lo pueda leer en el entorno de pruebas
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { validarPlaca, calcularTarifa };
}