import gtk

self.text_col = 0

class CompletedEntry(gtk.Entry):
    def __init__(self, text_col=0):
        gtk.Entry.__init__(self)
        self.text_col = text_col
        completion = gtk.EntryCompletion()
        completion.set_match_func(self.match_func)
        completion.connect("match-selected",
                            self.on_completion_match)
        completion.set_model(gtk.ListStore(str))
        completion.set_text_column(self.text_col)
        self.set_completion(completion)

    def match_func(self, completion, key, iter):
        model = completion.get_model()
        return model[iter][self.text_col].startswith(self.get_text())

    def on_completion_match(self, completion, model, iter):
        self.set_text(model[iter][self.text_col])
        self.set_position(-1)

    def add_words(self, words):
        model = self.get_completion().get_model()
        for word in words:
            model.append([word])

if __name__ == "__main__":
    win = gtk.Window()
    win.connect('delete-event', gtk.main_quit)

    entry = CompletedEntry()
    entry.add_words(['install', 'remove', 'erase'])
    win.add(entry)
    win.show_all()

    gtk.main()

