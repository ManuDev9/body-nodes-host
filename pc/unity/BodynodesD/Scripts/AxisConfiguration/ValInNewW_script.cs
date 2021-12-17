/**
* MIT License
* 
* Copyright (c) 2019-2021 Manuel Bottini
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:

* The above copyright notice and this permission notice shall be included in all
* copies or substantial portions of the Software.

* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*/

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class ValInNewW_script : MonoBehaviour {

	private GameObject virtualBodynodeToConfigure;
	private Button thisButton;
	private Text thisText;

	void changeSign(){
		if (thisText.text [0] == 'x') {
			thisText.text = 'y'.ToString ();
		} else if (thisText.text [0] == 'y') {
			thisText.text = 'z'.ToString ();
		} else if (thisText.text [0] == 'z') {
			thisText.text = 'w'.ToString ();
		} else {
			thisText.text = 'x'.ToString ();
		}
		virtualBodynodeToConfigure.GetComponent<BodynodeControllerX>().mMainPlayer.setAxisVal('w', thisText.text[0]);
		virtualBodynodeToConfigure.GetComponent<BodynodeControllerX>().resetPosition();
	}

	// Use this for initialization
	void Start () {
		thisButton = GetComponent<Button> ();
		thisText=thisButton.GetComponentInChildren<Text> ();
		thisText.text = 'w'.ToString();
		thisButton.onClick.AddListener (changeSign);
		virtualBodynodeToConfigure = gameObject.transform.parent.gameObject.GetComponent<CanvasScript>().virtualBodynodeToConfigure;
	}

	// Update is called once per frame
	void Update () {

	}
}
