from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Lista para armazenar os eventos temporariamente
eventos = []

@app.route("/", methods=["GET", "POST"])
def index():
    """Página inicial: exibe e adiciona eventos."""
    if request.method == "POST":
        evento = {
            "numero_sei": request.form["numero_sei"],
            "tipo": request.form["tipo"],
            "data_inicio": request.form["data_inicio"],
            "data_fim": request.form["data_fim"],
            "tecnicos": request.form["tecnicos"],
            "equipamentos": request.form["equipamentos"],
            "tombamentos": request.form["tombamentos"]
        }
        eventos.append(evento)  # Adiciona o evento à lista
        return redirect("/")  # Redireciona para a página inicial após adicionar o evento

    return render_template("index.html", eventos=eventos)

@app.route("/editar/<int:index>", methods=["GET", "POST"])
def editar_evento(index):
    """Permite editar um evento existente."""
    if index < 0 or index >= len(eventos):
        return redirect("/")  # Evita erros caso o índice seja inválido

    if request.method == "POST":
        eventos[index] = {
            "numero_sei": request.form["numero_sei"],
            "tipo": request.form["tipo"],
            "data_inicio": request.form["data_inicio"],
            "data_fim": request.form["data_fim"],
            "tecnicos": request.form["tecnicos"],
            "equipamentos": request.form["equipamentos"],
            "tombamentos": request.form["tombamentos"]
        }
        return redirect("/")

    return render_template("editar.html", evento=eventos[index], index=index)

@app.route("/excluir/<int:index>")
def excluir_evento(index):
    """Exclui um evento existente."""
    if 0 <= index < len(eventos):
        eventos.pop(index)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
