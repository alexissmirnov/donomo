from django.contrib import admin
from donomo.archive.models import *

class MimeTypeAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',)
admin.site.register(MimeType, MimeTypeAdmin)

class ProcessAdmin(admin.ModelAdmin):
    pass
admin.site.register(Process, ProcessAdmin)

class NodeAdmin(admin.ModelAdmin):
    pass
admin.site.register(Node, NodeAdmin)

class ProcessorAdmin(admin.ModelAdmin):
    pass
admin.site.register(Processor, ProcessorAdmin)

class TagAdmin(admin.ModelAdmin):
    pass
admin.site.register(Tag, TagAdmin)

class DocumentAdmin(admin.ModelAdmin):
    pass
admin.site.register(Document, DocumentAdmin)

class MessageAdmin(admin.ModelAdmin):
    pass
admin.site.register(Message, MessageAdmin)

class ContactAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contact, ContactAdmin)

class AddressAdmin(admin.ModelAdmin):
    pass
admin.site.register(Address, AddressAdmin)

class PageAdmin(admin.ModelAdmin):
    pass
admin.site.register(Page, PageAdmin)

class AssetClassAdmin(admin.ModelAdmin):
    pass
admin.site.register(AssetClass, AssetClassAdmin)

class AssetAdmin(admin.ModelAdmin):
    pass
admin.site.register(Asset, AssetAdmin)

class QueryAdmin(admin.ModelAdmin):
    pass
admin.site.register(Query, QueryAdmin)

class AccountAdmin(admin.ModelAdmin):
    pass
admin.site.register(Account, AccountAdmin)

class AccountClassAdmin(admin.ModelAdmin):
    pass
admin.site.register(AccountClass, AccountClassAdmin)
