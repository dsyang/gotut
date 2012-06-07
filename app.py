import mmdgot

if __name__ == '__main__':
    if mmdgot.app.config['PORT']:
        mmdgot.app.run(port=int(mmdgot.app.config['PORT']))
    else:
        mmdgot.app.run()
