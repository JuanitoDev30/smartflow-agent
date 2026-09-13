"""Nucleo del agente: el bucle de herramientas.

Es deliberadamente pequeno y explicito. No depende de ningun proveedor de LLM ni
de ningun canal: recibe texto del cliente y devuelve texto, ejecutando las
herramientas que el modelo pida por el camino.

Decisiones de diseno relevantes:

- El prompt de sistema es completamente estatico. El estado volatil (carrito,
  datos del cliente) NO se mete ahi, porque invalidaria la cache del prefijo en
  cada turno; se inyecta en el mensaje del turno actual, que nunca se cachea.
- Ese preambulo de estado no se guarda en el historial: se arma al vuelo. Asi el
  historial no acumula copias contradictorias del carrito.
- El bucle tiene tope de iteraciones. Un agente sin tope es una factura abierta.
"""


