# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from atmosphere import settings
from uuid import uuid5, UUID

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        def get_usergroup(user):
            groups = orm.Group.objects.filter(name=user.username)
            if not groups:
                return None
            return groups[0]

        def create_app(pm):
            m = pm.machine
            app = orm.Application()
            app.name = m.name
            app.description=m.description
            app.featured = m.featured
            app.icon = m.icon
            app.private = m.private
            app.created_by = m.created_by
            app.created_by_identity=m.created_by_identity
            app_uuid = uuid5(settings.ATMOSPHERE_NAMESPACE_UUID, str(pm.identifier))
            app.uuid = str(app_uuid)
            if orm.Application.objects.filter(uuid=app_uuid):
                print 'Skipping Duplicate ProviderMachine:%s' % pm.identifier
                return
            print '> UUID:%s Application:%s ImageID:%s' % (app.uuid, app.name, pm.identifier)
            app.save()
            if pm.end_date:
                app.end_date = timezone.now()

            if m.private:
                app_membership = orm.ApplicationMembership()    
                app_membership.application = app
                app_membership.group = get_usergroup(app.created_by)
                app_membership.can_edit = True
                app_membership.save()

            pm.application = app
            pm.save()

        for pm in orm.ProviderMachine.objects.all():
            gen_mach = pm.machine
            app = orm.Application.objects.filter(name=gen_mach.name)
            if not app:
                create_app(pm)
                continue
            app = app[0]
            #Calculate hash from the provider machine
            app_uuid = uuid5(settings.ATMOSPHERE_NAMESPACE_UUID, str(pm.identifier))
            app.uuid = str(app_uuid)
            if orm.Application.objects.filter(uuid=app_uuid):
                print 'Skipping Duplicate ProviderMachine:%s' % pm.identifier
                continue
            app.description=gen_mach.description
            app.icon=gen_mach.icon
            app.private=gen_mach.private
            app.featured=gen_mach.featured
            app.start_date=gen_mach.start_date
            app.created_by=gen_mach.created_by
            app.created_by_identity=gen_mach.created_by_identity
            print '> UUID:%s Application:%s ImageID:%s' % (app.uuid, app.name, pm.identifier)
            app.save()
            pm.application = app
            pm.save()
            if gen_mach.tags.all():
                print 'Porting tags from machine to application %s' % app.name
                for tag in gen_mach.tags.all():
                    tag.application_set.add(app)
        # There should be 0 that have a blank uuid, but they must be deleted to
        # ensure uniqueness
        for app in orm.Application.objects.filter(uuid=""):
            app.delete()
    def backwards(self, orm):
        "Write your backwards methods here."
        for pm in orm.ProviderMachine.objects.all():
            app = pm.application
            gen_mach = orm.Machine()
            gen_mach.description=app.description
            gen_mach.icon=app.icon
            gen_mach.private=app.private
            gen_mach.featured=app.featured
            gen_mach.start_date=app.start_date
            gen_mach.created_by=app.created_by
            gen_mach.created_by_identity=app.created_by_identity
            gen_mach.save()
            pm.machine = gen_mach
            pm.save()
            if gen_mach.tags.all():
                print 'Porting tags from machine to application %s' % app.name
                for tag in gen_mach.tags.all():
                    tag.application_set.add(app)

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.accountprovider': {
            'Meta': {'object_name': 'AccountProvider', 'db_table': "'provider_admin'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"})
        },
        'core.allocation': {
            'Meta': {'object_name': 'Allocation', 'db_table': "'allocation'"},
            'delta': ('django.db.models.fields.IntegerField', [], {'default': '20160', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'threshold': ('django.db.models.fields.IntegerField', [], {'default': '10080', 'null': 'True', 'blank': 'True'})
        },
        'core.application': {
            'Meta': {'object_name': 'Application', 'db_table': "'application'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'default': "''"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Tag']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'core.applicationmembership': {
            'Meta': {'unique_together': "(('application', 'group'),)", 'object_name': 'ApplicationMembership', 'db_table': "'application_membership'"},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Application']"}),
            'can_edit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'core.atmosphereuser': {
            'Meta': {'object_name': 'AtmosphereUser', 'db_table': "'atmosphere_user'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'selected_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'core.credential': {
            'Meta': {'object_name': 'Credential', 'db_table': "'credential'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.flow': {
            'Meta': {'object_name': 'Flow', 'db_table': "'flow'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'}),
            'status': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.FlowType']"})
        },
        'core.flowtype': {
            'Meta': {'object_name': 'FlowType', 'db_table': "'flowtype'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        },
        'core.group': {
            'Meta': {'object_name': 'Group', 'db_table': "'group'", '_ormbases': [u'auth.Group']},
            'applications': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Application']", 'symmetrical': 'False', 'through': "orm['core.ApplicationMembership']", 'blank': 'True'}),
            u'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'}),
            'identities': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Identity']", 'symmetrical': 'False', 'through': "orm['core.IdentityMembership']", 'blank': 'True'}),
            'instances': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Instance']", 'symmetrical': 'False', 'through': "orm['core.InstanceMembership']", 'blank': 'True'}),
            'leaders': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.AtmosphereUser']", 'through': "orm['core.Leadership']", 'symmetrical': 'False'}),
            'providers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Provider']", 'symmetrical': 'False', 'through': "orm['core.ProviderMembership']", 'blank': 'True'})
        },
        'core.identity': {
            'Meta': {'object_name': 'Identity', 'db_table': "'identity'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"})
        },
        'core.identitymembership': {
            'Meta': {'object_name': 'IdentityMembership', 'db_table': "'identity_membership'"},
            'allocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Allocation']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']"}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            'quota': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Quota']"})
        },
        'core.instance': {
            'Meta': {'object_name': 'Instance', 'db_table': "'instance'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider_alias': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'provider_machine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ProviderMachine']"}),
            'shell': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'vnc': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'core.instancemembership': {
            'Meta': {'object_name': 'InstanceMembership', 'db_table': "'instance_membership'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"})
        },
        'core.instancestatus': {
            'Meta': {'object_name': 'InstanceStatus', 'db_table': "'instance_status'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'core.instancestatushistory': {
            'Meta': {'object_name': 'InstanceStatusHistory', 'db_table': "'instance_status_history'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.InstanceStatus']"})
        },
        'core.leadership': {
            'Meta': {'object_name': 'Leadership', 'db_table': "'group_leaders'"},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"})
        },
        'core.machine': {
            'Meta': {'object_name': 'Machine', 'db_table': "'machine'"},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Application']", 'null': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'providers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Provider']", 'symmetrical': 'False', 'through': "orm['core.ProviderMachine']", 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Tag']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'core.machineexport': {
            'Meta': {'object_name': 'MachineExport', 'db_table': "'machine_export'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'export_file': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'export_format': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'export_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'export_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.machinerequest': {
            'Meta': {'object_name': 'MachineRequest', 'db_table': "'machine_request'"},
            'access_list': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'exclude_files': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'installed_software': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']"}),
            'iplant_sys_files': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'new_machine': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_machine'", 'null': 'True', 'to': "orm['core.ProviderMachine']"}),
            'new_machine_description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'new_machine_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'new_machine_owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            'new_machine_provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'new_machine_tags': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'new_machine_visibility': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'parent_machine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ancestor_machine'", 'to': "orm['core.ProviderMachine']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.maintenancerecord': {
            'Meta': {'object_name': 'MaintenanceRecord', 'db_table': "'maintenance_record'"},
            'disable_login': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']", 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.nodecontroller': {
            'Meta': {'object_name': 'NodeController', 'db_table': "'node_controller'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': '22'}),
            'private_ssh_key': ('django.db.models.fields.TextField', [], {}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        },
        'core.platformtype': {
            'Meta': {'object_name': 'PlatformType', 'db_table': "'platform_type'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        },
        'core.provider': {
            'Meta': {'object_name': 'Provider', 'db_table': "'provider'"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ProviderType']"}),
            'virtualization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.PlatformType']"})
        },
        'core.providercredential': {
            'Meta': {'object_name': 'ProviderCredential', 'db_table': "'provider_credential'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'core.providermachine': {
            'Meta': {'object_name': 'ProviderMachine', 'db_table': "'provider_machine'"},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Application']", 'null': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']", 'null': 'True'}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'machine': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Machine']"}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        },
        'core.providermembership': {
            'Meta': {'object_name': 'ProviderMembership', 'db_table': "'provider_membership'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Group']"}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"})
        },
        'core.providersize': {
            'Meta': {'object_name': 'ProviderSize', 'db_table': "'provider_size'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'cpu': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disk': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'ram': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'core.providertype': {
            'Meta': {'object_name': 'ProviderType', 'db_table': "'provider_type'"},
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        },
        'core.quota': {
            'Meta': {'object_name': 'Quota', 'db_table': "'quota'"},
            'cpu': ('django.db.models.fields.IntegerField', [], {'default': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'memory': ('django.db.models.fields.IntegerField', [], {'default': '4', 'null': 'True', 'blank': 'True'}),
            'storage': ('django.db.models.fields.IntegerField', [], {'default': '50', 'null': 'True', 'blank': 'True'}),
            'storage_count': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'suspended_count': ('django.db.models.fields.IntegerField', [], {'default': '2', 'null': 'True', 'blank': 'True'})
        },
        'core.size': {
            'Meta': {'object_name': 'Size', 'db_table': "'size'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'cpu': ('django.db.models.fields.IntegerField', [], {}),
            'disk': ('django.db.models.fields.IntegerField', [], {}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mem': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        },
        'core.step': {
            'Meta': {'object_name': 'Step', 'db_table': "'step'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']"}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'exit_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'flow': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Flow']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Instance']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'script': ('django.db.models.fields.TextField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        },
        'core.tag': {
            'Meta': {'object_name': 'Tag', 'db_table': "'tag'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']", 'null': 'True', 'blank': 'True'})
        },
        'core.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "'user_profile'"},
            'background': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '255'}),
            'default_size': ('django.db.models.fields.CharField', [], {'default': "'m1.small'", 'max_length': '255'}),
            'icon_set': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '255'}),
            'quick_launch': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'send_emails': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.AtmosphereUser']", 'unique': 'True', 'primary_key': 'True'}),
            'vnc_resolution': ('django.db.models.fields.CharField', [], {'default': "'800x600'", 'max_length': '255'})
        },
        'core.volume': {
            'Meta': {'object_name': 'Volume', 'db_table': "'volume'"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.AtmosphereUser']", 'null': 'True'}),
            'created_by_identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Identity']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Provider']"}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 1, 8, 0, 0)'})
        }
    }

    complete_apps = ['core']
    symmetrical = True