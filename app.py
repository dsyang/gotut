import mmdgot

if __name__ == '__main__':
    if mmdgot.app.config['PORT']:
        mmdgot.app.run(host="0.0.0.0", port=int(mmdgot.app.config['PORT']))
    else:
        mmdgot.app.run()
