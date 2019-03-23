from django.shortcuts import render, redirect
from django.http import HttpResponse
import dropbox
import json
import os
from . import crypto


def landing_page(request):
    return render(request, "secure_cloud/index.html")


def view_files(request):
    def process_folder_entries(current_state, entries):
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                current_state[entry.path_lower] = entry
            elif isinstance(entry, dropbox.files.DeletedMetadata):
                current_state.pop(entry.path_lower, None)
        return current_state

    with open("secure_cloud/config.json", "r") as f:
        data = json.load(f)

    dbx = dropbox.Dropbox(data["access"])
    result = dbx.files_list_folder(path="")

    files = process_folder_entries({}, result.entries)

    # check for and collect any additional entries
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files = process_folder_entries(files, result.entries)

    filenames = [[file[1:]] for file in sorted(files)]
    for filename in filenames:
        filename.append("/files/download/" + filename[0])

    context = {"filenames": filenames}

    return render(request, "secure_cloud/files_list.html", context)


def download_file(request, filename):
    with open("secure_cloud/config.json", "r") as f:
        data = json.load(f)
    dbx = dropbox.Dropbox(data["access"])

    metadata, f = dbx.files_download('/' + filename)

    response = HttpResponse(f.content)
    response['content_type'] = ''
    response['Content-Disposition'] = 'attachment;filename={}'.format(filename)
    return response


def upload_file(request):
    if request.method == 'POST' and request.FILES['upfile']:
        up_file = request.FILES['upfile']

        with open("secure_cloud/config.json", "r") as f:
            data = json.load(f)
        dbx = dropbox.Dropbox(data["access"])
        sym_key = data["keys"]["symmetric"]

        enc_up_file = crypto.encrypt_file(sym_key, up_file.file)

        file_to = "/{}".format(up_file.name)
        dbx.files_upload(enc_up_file, file_to)

    return redirect("view_files")


def generate_symmetric_key(request):
    key_length = 32
    # generate key using cryptographically secure pseudo-random number generator
    symmetric_key = os.urandom(key_length)

    with open("secure_cloud/config.json", "r+") as f:
        data = json.load(f)
        data["keys"]["symmetric"] = str(symmetric_key)

        f.seek(0)
        f.truncate()
        json.dump(data, f)

    return redirect("view_files")
