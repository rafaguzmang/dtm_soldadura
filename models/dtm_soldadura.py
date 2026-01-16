from odoo import api,models,fields
from datetime import datetime
import os
class Soldadura(models.Model):
    _name = "dtm.soldadura"
    _description = "Modulo para el proceso de soldadura"
    _rec_name = "orden_trabajo"

    orden_trabajo = fields.Integer(string='OT', readonly=True)
    revision_ot = fields.Integer(string='Versión', readonly=True)
    tipo_orden = fields.Char(string='Tipo', readonly=True)
    cliente = fields.Char(string='Cliente', readonly=True)
    product_name = fields.Char(string="Nombre",readonly=True)
    disenador = fields.Char(string='Diseñador', readonly=True)
    priority = fields.Selection([('0', 'Muy baja'), ('1', 'Baja'), ('2', 'Media'),('3', 'Alta'),('4', 'Muy alta')], string="Prioridad")
    planos_id = fields.One2many('dtm.soldadura.temporales', 'model_id')
    usuario = fields.Char()
    permiso = fields.Boolean(compute="_compute_permiso")

    def _compute_permiso(self):
        for record in self:
            record.usuario = self.env.user.partner_id.email
            record.permiso = False
            if record.usuario in ["rafaguzmang@hotmail.com", "calidad2@dtmindustry.com"]:
                record.permiso = True


    finalizado = fields.Boolean(compute="_compute_finalizado")
    status = fields.Float(compute="_compute_status")

    def _compute_status(self):
        for record in self:
            record.status = 0
            if record.maquinados_id:
                porcentaje = sum(record.maquinados_id.mapped('status'))
                servicios = len(record.maquinados_id.ids)
                record.status = porcentaje / servicios

    def _compute_finalizado(self):
        for record in self:
            record.finalizado = False
            if False not in record.maquinados_id.mapped('terminado'):
                record.finalizado = True

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Soldadura, self).get_view(view_id, view_type, **options)
        get_soldadura = self.env['dtm.proceso'].search([('status','=','soldadura')])
        for record in get_soldadura:
            # Se obtiene la información desde diseño
            get_diseno = self.env['dtm.odt'].search([('ot_number','=',record.ot_number),('revision_ot','=',record.revision_ot)],limit=1)
            vals = {
                'orden_trabajo':record.ot_number,
                'cliente':record.name_client,
                'product_name':get_diseno.product_name,
                'revision_ot':record.revision_ot,
                'tipo_orden':record.tipe_order,
                'disenador':get_diseno.disenador,
            }
            get_self = self.env['dtm.soldadura'].search([('orden_trabajo','=',record.ot_number),('revision_ot','=',record.revision_ot)],limit=1)
            if get_self:
                get_self.write(vals)
            else:
                get_self = self.env['dtm.soldadura'].create(vals)

            if record.anexos_id:
                for plano in get_diseno.anexos_id:
                    attachment = self.env['ir.attachment'].browse(plano.id)
                    vals = {
                        'model_id':get_self.id,
                        'nombre':attachment.name,
                        'archivo':attachment.datas,
                        'cantidad':get_diseno.cuantity
                    }
                    get_planos = self.env['dtm.soldadura.temporales'].search([('model_id','=',get_self.id),('nombre','=',plano.name)],limit=1)
                    get_planos.write(vals) if get_planos else get_planos.create(vals)

        return res

    def action_finalizar(self):
            vals = {
                'orden_trabajo':self.orden_trabajo,
                'revision_ot':self.revision_ot,
                'tipo_orden':self.tipo_orden,
                'cliente':self.cliente,
                'product_name':self.product_name,
                'disenador':self.disenador,
                'fecha_solicitud':self.create_date,
            }
            # Se busca si ya está terminado
            terminados = self.env['dtm.soldadura.terminados'].search(
                [('orden_trabajo', '=', self.orden_trabajo), ('revision_ot', '=', self.revision_ot),
                 ('tipo_orden', '=', self.tipo_orden)])
            if terminados:
                terminados.write(vals)
            else:
                terminados = self.env['dtm.soldadura.terminados'].create(vals)
            for servicio in self.planos_id:
                vals = {
                    'model_id':terminados.id,
                    'nombre':servicio.nombre,
                    'archivo':servicio.archivo,
                    'contador':servicio.contador,
                    'soldador':dict(servicio._fields['soldador'].selection).get(servicio.soldador),
                }
                get_finalizados = self.env['dtm.soldadura.terminados.planos'].search([
                    ('model_id', '=', terminados.id),
                    ('nombre', '=', servicio.nombre)], limit=1)
                if get_finalizados:
                    get_finalizados.write(vals)
                else:
                    get_finalizados = self.env['dtm.soldadura.terminados.planos'].create(vals)
                for tiempo in servicio.tiempos_id:
                    tiempo.write({'model_id': None, 'model_id2': get_finalizados.id, })
                # servicio.unlink()
            procesos = self.env['dtm.proceso'].search(
                [('ot_number', '=', self.orden_trabajo), ('tipe_order', '=', self.tipo_orden),
                 ('revision_ot', '=', self.revision_ot)])
            if procesos:
                procesos.write({
                    'status': 'calidad'
                })
            # self.unlink()
            return self.env.ref('dtm_soldadura.dtm_soldadura_act_window').read()[0]

class Temporales(models.Model):
    _name = 'dtm.soldadura.temporales'
    _description = 'Modulo para relacionar los archivos  asociados a una orden'

    model_id = fields.Many2one('dtm.soldadura')
    nombre = fields.Char(string="Nombre", readonly=True)
    archivo = fields.Binary(string="Plano", readonly=True)
    cantidad = fields.Integer(string="Cantidad",readonly=True)

    start = fields.Boolean()
    contador = fields.Integer()
    soldador = fields.Selection(string='Soldador', selection=[  ('aaron','Aaron Manquero Cereceres'),('antonio','Jorge Antonio Manquero Cereceres'),('jose','José Guadalupe García Rentería'),
                                                                ('guerrero', 'José Guerrero Ugarte Maldonado'), ('luis', 'Luis Alonso Morales Quezada'),('daniel', 'Daniel Palacios Beltrán')           ],readonly=False)
    status = fields.Float()

    tiempos_id = fields.One2many('dtm.soldadura.tiempos','model_id', readonly = True)
    timer = fields.Datetime()
    tiempo_total = fields.Float(string="Tiempo", readonly=True)

    def action_inicio(self):
        self.start = True
        self.timer = datetime.today()

    def action_stop(self):
        self.start = False
        self.tiempos_id.create({
                    'model_id': self.id,
                    'tiempo': round((datetime.today() - self.timer).total_seconds() / 60.0, 4)
                })
        self.tiempo_total = sum(self.tiempos_id.mapped('tiempo'))

    def action_mas(self):
        self.contador += 1
        self.status = (self.contador * 100)/self.cantidad
        if self.contador >= self.cantidad:
            self.terminado = True
            self.action_stop()

    def action_menos(self):
        self.contador -= 1
        self.contador = max(self.contador, 0)
        get_laser = self.env['dtm.documentos.cortadora'].search([('nombre', '=', self.nombre)], limit=1)
        get_laser.write({
            'contador': self.contador,
            'cortado': max(self.contador, 0),
            'status': self.status,
        })

class Tiempos(models.Model):
    _name = "dtm.soldadura.tiempos"
    _description = "Modelo para llevar el tiempo del trabajo de las máquinas laser"
    _order = "id desc"
    model_id = fields.Many2one('dtm.soldadura.temporales')
    model_id2 = fields.Many2one('dtm.soldadura.terminados.planos')

    tiempo = fields.Float(string='Duración', readonly=True)
