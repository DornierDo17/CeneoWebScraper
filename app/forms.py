from wtforms import Form, StringField, SubmitField, validators

class ExtractForm(Form):
    product_id = StringField("Product id", name="product_id", id="product_id", validators=[validators.DataRequired(message="Produc id is required"), 
                                                         validators.Length(min=6, max=10, message="Product id should be between 6 and 10 chars"),
                                                         validators.Regexp('^[0-9]+$', message="Product id can contain only digits")])
    submit = SubmitField("Extract opinions")