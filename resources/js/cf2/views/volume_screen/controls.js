Atmo.Views.VolumeScreenControls = Backbone.View.extend({
	'tagName': 'div',
	'className' : 'row-fluid',
	template: _.template(Atmo.Templates.volume_screen_controls),
	events: {
        'change select[name="all_volumes"]' : 'volume_form_completer',
        'click form[name="attach_detach_volume"] button' : 'attach_or_detach_volume',
		'submit form[name="create_volume_form"]' : 'create_volume',
		'keyup input[name="new_volume_name"], input[name="new_volume_size"]' : 'new_volume_form_activator',
		'click input[name="new_volume_size"]' : 'show_quota',
		'blur input[name="new_volume_size"]' : 'hide_quota',
		'change input[name="new_volume_size"]' : 'add_usage'
	},
	initialize: function() {
		Atmo.volumes.bind("reset", this.render, this);
		Atmo.instances.bind("add", this.render, this);
		Atmo.instances.bind("remove", this.render, this);
		Atmo.instances.bind("change", this.render, this);
		Atmo.volumes.bind("add", this.render, this);
		Atmo.volumes.bind("remove", this.render, this);
		Atmo.volumes.bind("change", this.render, this);
	},
	render: function() {
		this.$el.html(this.template());
		
        var self = this;

        var available_instances = 0, pending_instances = 0;

        for (var i = 0; i < Atmo.instances.models.length; i++) {
            if (Atmo.instances.models[i].get('state_is_active')) {
                available_instances++;
            }
            else if (Atmo.instances.models[i].get('state_is_build')) {
                pending_instances++;
            }
        }

        if (available_instances > 0) {
            $.each(Atmo.volumes.models, function(i, volume) {

                var volume_option = $('<option>', {
                    value: volume.get('id'),
                    html: volume.get('name_or_id')
                }).data('status', volume.get('status'));

                self.$el.find('select[name="all_volumes"]').append(volume_option);
            });
        }

        if (Atmo.volumes.models.length > 0 && available_instances > 0) {
            self.$el.find('select[name="all_volumes"]').removeAttr('disabled');
            self.$el.find('select[name="all_volumes"]').children().eq(0).html('Choose a Volume').attr('disabled', 'disabled');
        }
        if (available_instances == 0 && Atmo.volumes.models.length > 0) {
            self.$el.find('select[name="all_volumes"]').hide();
            self.$el.find('select[name="all_volumes"]').after($('<span>', {
                html: function() {
                    // User has no instances whatsoever
                    if (Atmo.instances.models.length == 0) {
                        var content = 'You need at least one running instance to use a volume.<br />';
                        content += '<a href="#new_instance">Launch New Instance</a>';
                    }
                    // User has instances, but they are pending or shutting down
                    else {
                        var content = 'Volumes can only be attached to active instances.'; 

                        // Suggest the proper course of action to enable this field, based on instance states
                        if (pending_instances > 0) {
                            content += '<br />Please wait for an instance\'s state icon to turn green.';
                        }
                        else {
                            content += '<br /><a href="#new_instance">Launch New Instance</a>';
                        }
                    }
                    return content;
                }
            }));
        }
        else {
            self.$el.find('select[name="all_volumes"]').show();
            self.$el.find('form[name="attach_detach_volume"]').find('span').remove();
        }

		return this;
	},
	show_quota: function() {
		// Populate the volume quota container
		this.$el.find('input[name="new_volume_size"]').popover({
            title: 'My Storage Quota <a class="close" data-parent="input[name=\'new_volume_size\']" data-dismiss="popover" href="#volumes">&times</a>',
			placement: 'bottom',
			trigger: 'manual',
			html: true,
			content: '<div id="disk_countHolder"></div><div id="disk_countHolder_info"></div><div id="diskHolder"></div><div id="diskHolder_info"></div>'
		});
		this.$el.find('input[name="new_volume_size"]').popover('show');

		this.disk_resource_chart = new Atmo.Views.ResourceCharts({
			el: this.$el.find('#diskHolder'), 
			quota_type: 'disk'
		}).render();
		this.disk_count_resource_chart = new Atmo.Views.ResourceCharts({
			el: this.$el.find('#disk_countHolder'), 
			quota_type: 'disk_count'
		}).render();

		this.$el.find('input[name="new_volume_size"]').trigger('change');
	},
	hide_quota: function() {
		this.$el.find('input[name="new_volume_size"]').popover('hide');
	},
	add_usage: function() {

        // If user clicks arrow instead of clicking in the box at first, change is triggered before focus.
        // So, force render and THEN return to add_usage method. 
        if (!this.disk_resource_chart) {
            this.show_quota();
            return;
        }

		var to_add;

		if (this.$el.find('input[name="new_volume_size"]').val().length == 0) {
			to_add = 0;
			count_add = 0;
		}
		else {			
			to_add = parseInt(this.$el.find('input[name="new_volume_size"]').val());
			count_add = 1;
		}

		if (to_add > 0) {

			console.log("to add", to_add);

			var disk_under_quota = this.disk_resource_chart.add_usage(to_add);
			var disk_count_under_quota = this.disk_count_resource_chart.add_usage(count_add);

			if (disk_under_quota && disk_count_under_quota)
				this.$el.find('button[name="create_volume"]').removeAttr('disabled');
			else
				this.$el.find('button[name="create_volume"]').attr('disabled', 'disabled');
		}
		else {
			console.log("to add", to_add);

			this.disk_resource_chart.render();
			this.disk_count_resource_chart.render();
		}
	},
    volume_form_completer: function(e) {
        var selected_volume = this.$el.find('select[name="all_volumes"] option').filter(':selected');
        var volume_form = this.$el.find('form[name="attach_detach_volume"]');
        var operation = (selected_volume.data('status') == 'in-use') ? 'Detach' : 'Attach';
  
        // Append a button at the end if it's already there. Otherwise, just change the button's html appropriately.  
        if (volume_form.find('button').length == 0) {
            volume_form.append($('<button>', {
                html: operation,
                class: 'btn'
            }));
        }
        else {
            volume_form.find('button').html(operation);
        }

        // If the volume must be attached, determine whether or not you need to add another select box
        if (operation == 'Detach' && volume_form.find('select').length == 2) {
            volume_form.find('select').eq(1).remove();
        }
        if (operation == 'Attach' && volume_form.find('select').length == 1) {

            var available_instances = $('<select>', {
                name: 'running_instances'
            });

            for (var i = 0; i < Atmo.instances.models.length; i++) {
                if (Atmo.instances.models[i].get('state_is_active')) {
                    available_instances.append($('<option>', {
                        value: Atmo.instances.models[i].get('id'),
                        html: Atmo.instances.models[i].get('name_or_id')
                    }));
                }
            }

            this.$el.find('select[name="all_volumes"]').after(available_instances);
        } 


    },
    attach_or_detach_volume: function(e) {
        e.preventDefault();

        var selected_volume = this.$el.find('select[name="all_volumes"] option').filter(':selected');
        var volume_status = selected_volume.data('status');

        var selected_instance = this.$el.find('select[name="running_instances"] option').filter(':selected');
        var instance_id = selected_instance.val();

        if (volume_status == 'in-use') {
           this.detach_volume(selected_volume.val()); 
        }
        else if (volume_status == 'available') {
            this.attach_volume(selected_volume.val(), instance_id);
        }
    },
	attach_volume: function(volume_id, instance_id) {
		var self = this;
        var selected_volume = Atmo.volumes.get(volume_id);
        var selected_instance = Atmo.instances.get(instance_id);
        Atmo.Utils.attach_volume(selected_volume, selected_instance, {
			success: function() {
				self.render;
			},
			error: function() {
				Atmo.Utils.notify("Could not attach volume", 'If the problem persists, please email <a href="mailto:support@iplantcollaborative.org">support@iplantcollaborative.org</a>', { no_timeout: true });
			},
		});
	},
    detach_volume: function(volume_id) {
        var selected_volume = Atmo.volumes.get(volume_id);
        var selected_instance = Atmo.instances.get(selected_volume.get("attach_data_instance_id"));

        Atmo.Utils.confirm_detach_volume(selected_volume, selected_instance);
    },
	create_volume: function(e) {
        //Prevents double-clicking the button..
        this.$el.find('button[name="create_volume"]').attr('disabled', 'disabled');

		e.preventDefault();

		var params = {
			'name' : $('input[name="new_volume_name"]').val().trim(),
			'size' : parseInt($('input[name="new_volume_size"]').val()),
			'tags' : 'CF++',
			'description' : ''
		};

		var errors = [];

		var disk_count_under_quota = this.disk_count_resource_chart.add_usage(1);

		if (!disk_count_under_quota) {
			errors.push("You have already created all of your allocated volumes. Delete an existing volume or request more resources.");
		}
		if (params['name'].length < 1 || params['name'].length > 50) {
			errors.push("Volume name must be between 1 and 50 characters.");
		}
		if (!/^[a-z]([0-9a-z_])*$/i.test(params['name'])) { 
			errors.push("Volume name must begin with a letter and contain only alaphumeric characters and underscores.");
		}
		if (params['size'] > 100 || params['size'] < 1) {
			errors.push("Volume size must be between 1 GB and 100 GB.");
		}

		if (errors.length == 0) {
			var volume = new Atmo.Models.Volume();
			var self = this;
			volume.save(params, {
				wait: true,
				success: function(model) {
					Atmo.volumes.add(model);
					Atmo.Utils.notify("New volume created!", "Your volume will be ready to attach to an instance momentarily.");
					Backbone.history.navigate('#volumes', {trigger: true, replace: true});
					self.$el.find('input[name="new_volume_name"]').val("").focus().trigger('keyup');
					self.$el.find('input[name="new_volume_size"]').val("0");
				},
				error: function() {
					Atmo.Utils.notify("Could not create volume", 'If the problem persists, please email <a href="mailto:support@iplantcollaborative.org">support@iplantcollaborative.org</a>', { no_timeout: true });
				},
			});
		}
		else {
			Atmo.Utils.notify("Errors with Volume Creation", errors.join(', '));
            this.$el.find('button[name="create_volume"]').removeAttr('disabled');
		}

	},
	new_volume_form_activator: function(e) {

		if ($('input[name="new_volume_size"]').is(':focus')) 
			this.add_usage();

		var volume_name = this.$el.find('input[name="new_volume_name"]').val();
		var volume_size = this.$el.find('input[name="new_volume_size"]').val();

		var volume_name_field = this.$el.find('input[name="new_volume_name"]');
		var volume_size_field = this.$el.find('input[name="new_volume_size"]');

		this.$el.find('#volume_creation_errors').html("<ul></ul>");
		var errors = false;

		// Make sure volume name doesn't contain spaces
		if (volume_name.length > 0 && volume_name.indexOf(' ') != -1) {
			// Tell them there's a problem
			this.$el.find('#volume_creation_errors ul').append("<li>Volume names may not contain spaces.</li>");
			volume_name_field.addClass('error');
			this.$el.find('button[name="create_volume"]').attr('disabled', 'disabled');
			errors = true;
		}
		var exp = /^[a-zA-Z0-9_]*$/gi;
		if (exp.test(volume_name) == false) {
			this.$el.find('#volume_creation_errors ul').append("<li>Volume name may contain only numbers, letters, and underscores.</li>");
			this.$el.find('button[name="create_volume"]').attr('disabled', 'disabled');
			volume_name_field.addClass('error');
			errors = true;
		}

		if (!errors) {
			// No errors yet means that volume_name is ok
			volume_name_field.removeClass('error');
		}

		if (volume_size.length > 0 && parseInt(volume_size) > 100) {
			errors = true;
			this.$el.find('#volume_creation_errors ul').append("<li>Volume size may not exceed 100 GB.</ul>");
			volume_size_field.parent().addClass('error');
			this.$el.find('button[name="create_volume"]').attr('disabled', 'disabled');
		}
		else if (Atmo.volumes.length + 1 > Atmo.profile.get('selected_identity').get('quota').disk_count) {
			if (volume_name.length > 0 && volume_name.indexOf(' ') == -1) {
				errors = true;
				this.$el.find('#volume_creation_errors ul').append('<li>You have already created all of your allocated volumes.</li>');
				volume_name_field.addClass('error');
				this.$el.find('button[name="create_volume"]').attr('disabled', 'disabled');
			}
		}
		else {
			volume_size_field.parent().removeClass('error');
		}

		if (volume_name.length > 0 && volume_size.length > 0) {

			if (!errors) {
				this.$el.find('button[name="create_volume"]').removeAttr('disabled');
				this.$el.find('#volume_creation_errors').html("");
				
				volume_name_field.removeClass('error');
				volume_size_field.parent().removeClass('error');
			}
			else {
				resizeApp();
			}
		}

	},
});