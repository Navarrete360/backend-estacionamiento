// test/frontend.test.js
const test = require('unit.js');
const { validarPlaca, calcularTarifa } = require('../logic.js');

describe('Pruebas Unitarias del Frontend (logic.js)', function() {

    describe('1. Módulo de Validación de Placas', function() {
        it('Debe aceptar una placa estándar de 6 caracteres (ej. QOM-434)', function() {
            // Unit.js verifica que el resultado sea TRUE
            test.bool(validarPlaca('QOM-434')).isTrue();
        });

        it('Debe rechazar una placa con menos de 6 caracteres', function() {
            test.bool(validarPlaca('ABC12')).isFalse();
        });

        it('Debe rechazar placas con caracteres especiales no permitidos', function() {
            test.bool(validarPlaca('QOM_434!')).isFalse();
        });
    });

    describe('2. Módulo de Cálculo de Tarifas', function() {
        it('Debe cobrar S/ 5.00 por la primera hora o fracción', function() {
            test.number(calcularTarifa(0.5)).isIdenticalTo(5.00);
        });

        it('Debe cobrar S/ 15.00 por 2.5 horas de estadía (redondeo a 3 horas)', function() {
            test.number(calcularTarifa(2.5)).isIdenticalTo(15.00);
        });
    });
});