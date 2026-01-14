from odoo import fields, models, api


class Terminado(models.Model):
    _name = "dtm.soldadura.terminados"
    _description = "Modelo para llevar el registro de las ordenes soldadas"
    _rec_name = "orden_trabajo"

    orden_trabajo = fields.Integer(string='OT', readonly=True)
    revision_ot = fields.Integer(string='Versión', readonly=True)
    tipo_orden = fields.Char(string='Tipo', readonly=True)
    cliente = fields.Char(string='Cliente', readonly=True)
    product_name = fields.Char(string="Nombre", readonly=True)
    disenador = fields.Char(string='Diseñador', readonly=True)
    fecha_solicitud = fields.Datetime(string='Fecha de Solicityd',readonly=True)

    planos_id = fields.One2many('dtm.soldadura.terminados.planos', 'model_id',readonly=True)

    # usuario = fields.Char()
    # permiso = fields.Boolean(compute="_compute_permiso")

    # def _compute_duracion(self):
    #     for result in self:
    #         result.duracion = round((result.create_date - result.fecha_solicitud).total_seconds() / 3600.0, 2)

class PlanosTerminados(models.Model):
    _name = "dtm.soldadura.terminados.planos"
    _description = "Modelo para guardar los planos que ya fueron soldados"
    _order = "id desc"

    model_id = fields.Many2one("dtm.soldadura.terminados")
    nombre = fields.Char(string="Nombre",readonly=True)
    archivo = fields.Binary(string="Archivo",readonly=True)
    contador = fields.Integer(string="Contador",readonly=True)
    soldador = fields.Char(string="Soldador",readonly=True)

    tiempos_id = fields.One2many('dtm.soldadura.tiempos','model_id2', readonly = True)



